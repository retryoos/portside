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
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol, runtime_checkable

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db import models as m
from .db.mapping import (
    _ensure_utc,
    orm_to_state,
    state_to_orm,
    update_orm_from_state,
)
from .objects import StoredDocument
from .analyst_citations import FlaggedEventCitations
from .legal.models import CitedAuthority
from .researcher import EvidenceItem
from .schemas import VesselSummary, VoyageState, VoyageSummary


# Non-terminal pipeline stages: a voyage here is mid-run. Past these it sits in
# a human-driven lifecycle (done/pending/...) and no longer advances on its own.
PROCESSING_STAGES: frozenset[str] = frozenset(
    {"uploaded", "extracting", "calculating", "analyzing", "drafting"}
)


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

    async def save_many(
        self, states: list[VoyageState], owner_user_id: str | None = None
    ) -> None:
        """Persist many voyages in ONE transaction (bulk seed). One connection
        and one commit, vs ``save`` per voyage which is one of each per call."""
        ...

    async def load(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> VoyageState | None: ...

    async def patch(self, voyage_id: str, /, **fields: Any) -> VoyageState | None: ...

    async def list(self, owner_user_id: str | None = None) -> list[VoyageSummary]: ...

    async def list_for_owners(
        self, owner_user_ids: list[str]
    ) -> list[VoyageSummary]:
        """Voyages owned by ANY of ``owner_user_ids`` (workspace sharing)."""
        ...

    async def load_for_owners(
        self, voyage_id: str, owner_user_ids: list[str]
    ) -> VoyageState | None:
        """Load a voyage iff its owner is in ``owner_user_ids``."""
        ...

    async def list_vessels(
        self, owner_user_id: str | None = None
    ) -> list[VesselSummary]: ...

    async def ensure_user(self, user_id: str, email: str | None = None) -> None: ...

    async def delete(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> bool: ...

    async def record_documents(
        self, voyage_id: str, documents: list[StoredDocument]
    ) -> None: ...

    async def list_documents(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[StoredDocument]: ...

    async def reap_stale_processing(self, older_than_seconds: int) -> int: ...

    async def record_evidence(
        self, voyage_id: str, items: list[EvidenceItem]
    ) -> None: ...

    async def list_evidence(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[EvidenceItem]: ...

    async def record_citations(
        self, voyage_id: str, items: list[FlaggedEventCitations]
    ) -> None: ...

    async def list_citations(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[FlaggedEventCitations]: ...


class InMemoryStore:
    """In-process dict implementation. No persistence (process restart clears it)."""

    def __init__(self) -> None:
        self._voyages: dict[str, VoyageState] = {}
        self._documents: dict[str, list[StoredDocument]] = {}
        self._evidence: dict[str, list[EvidenceItem]] = {}
        self._citations: dict[str, list[FlaggedEventCitations]] = {}
        self._lock = asyncio.Lock()

    async def save(
        self, state: VoyageState, owner_user_id: str | None = None
    ) -> None:
        async with self._lock:
            self._voyages[state.voyage_id] = state

    async def save_many(
        self, states: list[VoyageState], owner_user_id: str | None = None
    ) -> None:
        async with self._lock:
            for state in states:
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

    async def list_for_owners(
        self, owner_user_ids: list[str]
    ) -> list[VoyageSummary]:
        # The in-memory store does not track ownership; return everything.
        return await self.list()

    async def load_for_owners(
        self, voyage_id: str, owner_user_ids: list[str]
    ) -> VoyageState | None:
        return self._voyages.get(voyage_id)

    async def list_vessels(
        self, owner_user_id: str | None = None
    ) -> list[VesselSummary]:
        return vessels_from_summaries(await self.list())

    async def ensure_user(self, user_id: str, email: str | None = None) -> None:
        return None  # no user table in the in-memory store

    async def delete(self, voyage_id: str, owner_user_id: str | None = None) -> bool:
        async with self._lock:
            self._documents.pop(voyage_id, None)
            self._evidence.pop(voyage_id, None)
            self._citations.pop(voyage_id, None)
            return self._voyages.pop(voyage_id, None) is not None

    async def record_documents(
        self, voyage_id: str, documents: list[StoredDocument]
    ) -> None:
        async with self._lock:
            self._documents.setdefault(voyage_id, []).extend(documents)

    async def list_documents(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[StoredDocument]:
        return list(self._documents.get(voyage_id, []))

    async def reap_stale_processing(self, older_than_seconds: int) -> int:
        return 0  # single-process, ephemeral: nothing to recover

    async def record_evidence(
        self, voyage_id: str, items: list[EvidenceItem]
    ) -> None:
        async with self._lock:
            self._evidence.setdefault(voyage_id, []).extend(items)

    async def list_evidence(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[EvidenceItem]:
        return list(self._evidence.get(voyage_id, []))

    async def record_citations(
        self, voyage_id: str, items: list[FlaggedEventCitations]
    ) -> None:
        async with self._lock:
            self._citations.setdefault(voyage_id, []).extend(items)

    async def list_citations(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[FlaggedEventCitations]:
        return list(self._citations.get(voyage_id, []))


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
                if existing is None:
                    session.add(state_to_orm(state, owner_user_id))
                else:
                    # In-place update: replace the analysis branches, but keep
                    # owner (unless explicitly set) and the uploaded documents.
                    if owner_user_id is not None:
                        existing.owner_user_id = owner_user_id
                    # Drop the existing one-to-one analysis branches and flush
                    # the DELETEs before update_orm_from_state inserts the new
                    # ones. Each child has a UNIQUE(voyage_id); without this,
                    # SQLAlchemy's unit-of-work can order the new INSERT before
                    # the old DELETE in the same flush, which Postgres/asyncpg
                    # (Neon) rejects as a hard UniqueViolationError. This bites
                    # every multi-stage pipeline save (extracting -> calculating
                    # -> ... re-saves the extraction), failing the run with a
                    # generic "Processing failed unexpectedly".
                    existing.extraction = None
                    existing.laytime = None
                    existing.dispute = None
                    existing.packet = None
                    await session.flush()
                    update_orm_from_state(existing, state)

    async def save_many(
        self, states: list[VoyageState], owner_user_id: str | None = None
    ) -> None:
        # All voyages in ONE session + ONE transaction (one connection, one
        # commit), unlike ``save`` which opens a session per call. Used by the
        # demo-share seed so login does not pay N connect round trips. Same
        # upsert + flush-before-reinsert logic as ``save`` (see that comment).
        async with self._sm() as session:
            async with session.begin():
                for state in states:
                    existing = await session.get(m.Voyage, state.voyage_id)
                    if existing is None:
                        session.add(state_to_orm(state, owner_user_id))
                        continue
                    if owner_user_id is not None:
                        existing.owner_user_id = owner_user_id
                    existing.extraction = None
                    existing.laytime = None
                    existing.dispute = None
                    existing.packet = None
                    await session.flush()
                    update_orm_from_state(existing, state)

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
                # Lock the row for the read-modify-write so concurrent staged
                # writers (across instances) can't lose updates. FOR UPDATE is a
                # no-op on SQLite, which already serialises writes.
                existing = await session.get(
                    m.Voyage, voyage_id, with_for_update=True
                )
                if existing is None:
                    return None
                updated = orm_to_state(existing).model_copy(update=fields)
                # In-place update preserves owner + documents (not in VoyageState).
                update_orm_from_state(existing, updated)
            return updated

    async def list(
        self,
        owner_user_id: str | None = None,
        owner_user_ids: list[str] | None = None,
    ) -> list[VoyageSummary]:
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
        if owner_user_ids is not None:
            stmt = stmt.where(m.Voyage.owner_user_id.in_(list(owner_user_ids)))
        elif owner_user_id is not None:
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

    async def list_for_owners(
        self, owner_user_ids: list[str]
    ) -> list[VoyageSummary]:
        owners = list(owner_user_ids)
        if not owners:
            return []
        return await self.list(owner_user_ids=owners)

    async def load_for_owners(
        self, voyage_id: str, owner_user_ids: list[str]
    ) -> VoyageState | None:
        owners = set(owner_user_ids)
        async with self._sm() as session:
            voyage = await session.get(m.Voyage, voyage_id)
            if voyage is None or voyage.owner_user_id not in owners:
                return None
            return orm_to_state(voyage)

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

    async def record_documents(
        self, voyage_id: str, documents: list[StoredDocument]
    ) -> None:
        async with self._sm() as session:
            async with session.begin():
                for d in documents:
                    session.add(
                        m.VoyageDocumentRow(
                            voyage_id=voyage_id,
                            role=d.role,
                            object_key=d.object_key,
                            content_type=d.content_type,
                            size_bytes=d.size_bytes,
                        )
                    )

    async def list_documents(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[StoredDocument]:
        async with self._sm() as session:
            if owner_user_id is not None:
                voyage = await session.get(m.Voyage, voyage_id)
                if voyage is None or voyage.owner_user_id != owner_user_id:
                    return []
            rows = (
                await session.execute(
                    select(m.VoyageDocumentRow)
                    .where(m.VoyageDocumentRow.voyage_id == voyage_id)
                    .order_by(m.VoyageDocumentRow.role)
                )
            ).scalars().all()
        return [
            StoredDocument(
                role=r.role,
                object_key=r.object_key,
                content_type=r.content_type,
                size_bytes=r.size_bytes,
            )
            for r in rows
        ]

    async def record_evidence(
        self, voyage_id: str, items: list[EvidenceItem]
    ) -> None:
        async with self._sm() as session:
            async with session.begin():
                for it in items:
                    session.add(
                        m.VoyageEvidenceRow(
                            voyage_id=voyage_id,
                            event_id=it.event_id,
                            source=it.source,
                            observed_value=it.observed_value,
                            supports=it.supports,
                            citation=it.citation,
                            summary=it.summary,
                        )
                    )

    async def list_evidence(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[EvidenceItem]:
        async with self._sm() as session:
            if owner_user_id is not None:
                voyage = await session.get(m.Voyage, voyage_id)
                if voyage is None or voyage.owner_user_id != owner_user_id:
                    return []
            rows = (
                await session.execute(
                    select(m.VoyageEvidenceRow)
                    .where(m.VoyageEvidenceRow.voyage_id == voyage_id)
                    .order_by(m.VoyageEvidenceRow.id)
                )
            ).scalars().all()
        return [
            EvidenceItem(
                event_id=r.event_id,
                source=r.source,
                observed_value=r.observed_value,
                supports=r.supports,
                citation=r.citation,
                summary=r.summary,
            )
            for r in rows
        ]

    async def record_citations(
        self, voyage_id: str, items: list[FlaggedEventCitations]
    ) -> None:
        async with self._sm() as session:
            async with session.begin():
                for bundle in items:
                    for authority in bundle.cited_authorities:
                        session.add(
                            m.VoyageCitationRow(
                                voyage_id=voyage_id,
                                event_id=bundle.event_id,
                                citation=authority.citation,
                                tool_used=authority.tool_used,
                                proposition=authority.proposition,
                                url=authority.url,
                            )
                        )

    async def list_citations(
        self, voyage_id: str, owner_user_id: str | None = None
    ) -> list[FlaggedEventCitations]:
        async with self._sm() as session:
            if owner_user_id is not None:
                voyage = await session.get(m.Voyage, voyage_id)
                if voyage is None or voyage.owner_user_id != owner_user_id:
                    return []
            rows = (
                await session.execute(
                    select(m.VoyageCitationRow)
                    .where(m.VoyageCitationRow.voyage_id == voyage_id)
                    .order_by(m.VoyageCitationRow.id)
                )
            ).scalars().all()

        # Re-bucket the flat row list back into per-event bundles. Order is
        # preserved within an event (insertion order) and the events appear
        # in first-seen order, which mirrors how the route would have
        # iterated state.dispute.flagged_events.
        by_event: dict[str, list[CitedAuthority]] = {}
        for r in rows:
            by_event.setdefault(r.event_id, []).append(
                CitedAuthority(
                    citation=r.citation,
                    verified_via_tool=True,
                    tool_used=r.tool_used,  # type: ignore[arg-type]
                    proposition=r.proposition,
                    url=r.url,
                )
            )
        return [
            FlaggedEventCitations(event_id=event_id, cited_authorities=authorities)
            for event_id, authorities in by_event.items()
        ]

    async def reap_stale_processing(self, older_than_seconds: int) -> int:
        """Mark interrupted real uploads as errored.

        A voyage stuck in a non-terminal pipeline stage whose ``updated_at`` is
        older than the threshold had its driving task die with a prior instance.
        We only reap voyages that have uploaded documents, so the demo seeds
        (which carry processing-like stages but no documents) are never touched,
        and the threshold means an active run on another live instance — which
        keeps advancing ``updated_at`` — is safe.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)
        has_docs = exists().where(
            m.VoyageDocumentRow.voyage_id == m.Voyage.voyage_id
        )
        stmt = (
            update(m.Voyage)
            .where(
                m.Voyage.stage.in_(PROCESSING_STAGES),
                m.Voyage.updated_at < cutoff,
                has_docs,
            )
            .values(stage="error", error="processing interrupted")
        )
        async with self._sm() as session:
            async with session.begin():
                result = await session.execute(stmt)
        return result.rowcount or 0
