"""Voyage state storage.

Two implementations of the ``VoyageStore`` Protocol:

  * ``InMemoryStore`` — an in-process dict; used by tests and as an offline
    fallback. No durability.
  * ``SqlVoyageStore`` — the production store: the full ``VoyageState`` tree is
    persisted relationally (see ``db/models.py``) via SQLAlchemy async, so state
    survives a restart and is Postgres-ready (set ``DATABASE_URL``).

Both share the summary/vessel-aggregation helpers below so the dashboard
projections behave identically regardless of backend.

``owner_user_id`` is threaded through (the A2 auth seam) but is a no-op filter
for now — no caller passes it yet, and seeded/demo voyages own ``None``.

Staged-update contract (the pipeline writes progress through this):

    await store.save(VoyageState(voyage_id=..., perspective=..., stage="uploaded"))
    await store.patch(voyage_id, stage="extracting")
    ...
    await store.patch(voyage_id, stage="done", packet=packet)

``patch`` is a partial merge applied atomically (load -> model_copy -> persist in
one transaction) so concurrent pipeline tasks never interleave field updates.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol, runtime_checkable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db import models as m
from .db.mapping import _ensure_utc, orm_to_state, state_to_orm
from .schemas import VesselSummary, VoyageState, VoyageSummary


# --- shared projection helpers ---------------------------------------------


def summaries_from_states(states: list[VoyageState]) -> list[VoyageSummary]:
    """VoyageSummary rows, newest-first by ``created_at``."""
    ordered = sorted(states, key=lambda s: s.created_at, reverse=True)
    return [VoyageSummary.from_state(s) for s in ordered]


def vessels_from_summaries(summaries: list[VoyageSummary]) -> list[VesselSummary]:
    """Group already newest-first summaries by ``vessel_name`` into vessels.

    Voyages with no vessel_name yet (still processing) are skipped. Vessels are
    ordered by their newest voyage, which falls out of iterating newest-first.
    """
    groups: dict[str, list[VoyageSummary]] = {}
    for s in summaries:
        if s.vessel_name is None:
            continue
        groups.setdefault(s.vessel_name, []).append(s)

    vessels: list[VesselSummary] = []
    for name, rows in groups.items():
        quantums = [r.quantum_eur for r in rows if r.quantum_eur is not None]
        newest = rows[0]  # rows inherit newest-first ordering
        vessels.append(
            VesselSummary(
                name=name,
                voyage_count=len(rows),
                total_quantum_eur=round(sum(quantums), 2) if quantums else None,
                latest_stage=newest.stage,
                last_activity=newest.created_at,
                perspectives=sorted({r.perspective for r in rows}),
            )
        )
    return vessels


@runtime_checkable
class VoyageStore(Protocol):
    """Async storage contract for voyage state."""

    async def save(
        self, state: VoyageState, owner_user_id: str | None = None
    ) -> None: ...

    async def load(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> VoyageState | None: ...

    async def patch(self, voyage_id: str, /, **fields: Any) -> VoyageState | None: ...

    async def list(self, owner_user_id: str | None = None) -> list[VoyageSummary]: ...

    async def list_vessels(
        self, owner_user_id: str | None = None
    ) -> list[VesselSummary]: ...

    async def ensure_user(self, user_id: str, email: str | None = None) -> None: ...

    async def delete(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> bool: ...


class InMemoryStore:
    """In-process dict implementation. No persistence (process restart clears it)."""

    def __init__(self) -> None:
        self._voyages: dict[str, VoyageState] = {}
        self._lock = asyncio.Lock()

    async def save(
        self, state: VoyageState, owner_user_id: str | None = None
    ) -> None:
        async with self._lock:
            self._voyages[state.voyage_id] = state

    async def load(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> VoyageState | None:
        return self._voyages.get(voyage_id)

    async def patch(self, voyage_id: str, /, **fields: Any) -> VoyageState | None:
        async with self._lock:
            existing = self._voyages.get(voyage_id)
            if existing is None:
                return None
            updated = existing.model_copy(update=fields)
            self._voyages[voyage_id] = updated
            return updated

    async def list(self, owner_user_id: str | None = None) -> list[VoyageSummary]:
        return summaries_from_states(list(self._voyages.values()))

    async def list_vessels(
        self, owner_user_id: str | None = None
    ) -> list[VesselSummary]:
        return vessels_from_summaries(await self.list())

    async def ensure_user(self, user_id: str, email: str | None = None) -> None:
        return None  # no user table in the in-memory store

    async def delete(self, voyage_id: str, owner_user_id: str | None = None) -> bool:
        async with self._lock:
            return self._voyages.pop(voyage_id, None) is not None


class SqlVoyageStore:
    """SQLAlchemy-async implementation of ``VoyageStore`` (SQLite or Postgres)."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sm = sessionmaker

    async def save(
        self, state: VoyageState, owner_user_id: str | None = None
    ) -> None:
        async with self._sm() as session:
            async with session.begin():
                existing = await session.get(m.Voyage, state.voyage_id)
                owner = owner_user_id
                if owner is None and existing is not None:
                    owner = existing.owner_user_id
                if existing is not None:
                    await session.delete(existing)
                    await session.flush()
                session.add(state_to_orm(state, owner))

    async def load(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> VoyageState | None:
        async with self._sm() as session:
            voyage = await session.get(m.Voyage, voyage_id)
            if voyage is None:
                return None
            if owner_user_id is not None and voyage.owner_user_id != owner_user_id:
                return None
            return orm_to_state(voyage)

    async def patch(self, voyage_id: str, /, **fields: Any) -> VoyageState | None:
        async with self._sm() as session:
            async with session.begin():
                existing = await session.get(m.Voyage, voyage_id)
                if existing is None:
                    return None
                owner = existing.owner_user_id
                updated = orm_to_state(existing).model_copy(update=fields)
                await session.delete(existing)
                await session.flush()
                session.add(state_to_orm(updated, owner))
            return updated

    async def list(self, owner_user_id: str | None = None) -> list[VoyageSummary]:
        stmt = (
            select(
                m.Voyage.voyage_id,
                m.Voyage.stage,
                m.Voyage.perspective,
                m.Voyage.created_at,
                m.CharterPartyRow.vessel_name,
                m.CharterPartyRow.load_port,
                m.CharterPartyRow.discharge_port,
                m.ClaimPacketRow.quantum_eur,
            )
            .outerjoin(m.Extraction, m.Extraction.voyage_id == m.Voyage.voyage_id)
            .outerjoin(
                m.CharterPartyRow,
                m.CharterPartyRow.extraction_id == m.Extraction.id,
            )
            .outerjoin(
                m.ClaimPacketRow, m.ClaimPacketRow.voyage_id == m.Voyage.voyage_id
            )
            .order_by(m.Voyage.created_at.desc())
        )
        if owner_user_id is not None:
            stmt = stmt.where(m.Voyage.owner_user_id == owner_user_id)
        async with self._sm() as session:
            rows = (await session.execute(stmt)).all()
        return [
            VoyageSummary(
                id=r.voyage_id,
                vessel_name=r.vessel_name,
                load_port=r.load_port,
                discharge_port=r.discharge_port,
                quantum_eur=r.quantum_eur,
                stage=r.stage,
                perspective=r.perspective,
                created_at=_ensure_utc(r.created_at),
            )
            for r in rows
        ]

    async def list_vessels(
        self, owner_user_id: str | None = None
    ) -> list[VesselSummary]:
        return vessels_from_summaries(await self.list(owner_user_id))

    async def ensure_user(self, user_id: str, email: str | None = None) -> None:
        async with self._sm() as session:
            async with session.begin():
                existing = await session.get(m.User, user_id)
                if existing is None:
                    session.add(m.User(id=user_id, email=email))
                elif email and existing.email != email:
                    existing.email = email

    async def delete(self, voyage_id: str, owner_user_id: str | None = None) -> bool:
        async with self._sm() as session:
            async with session.begin():
                voyage = await session.get(m.Voyage, voyage_id)
                if voyage is None:
                    return False
                if (
                    owner_user_id is not None
                    and voyage.owner_user_id != owner_user_id
                ):
                    return False
                await session.delete(voyage)
                return True
