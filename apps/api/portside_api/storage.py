"""Voyage state storage.

Hackathon-grade: a single in-process dict keyed by voyage_id. No persistence —
restarting the process clears all state, which is acceptable for the demo. The
``VoyageStore`` Protocol leaves room to swap in a real backend later without
touching call sites.

Staged-update contract (for the future per-stage pipeline integration that
Agent 2's PR will land):

    await store.save(VoyageState(voyage_id=..., perspective=..., stage="uploaded"))
    await store.patch(voyage_id, stage="extracting")
    extraction = await extractor.run(...)
    await store.patch(voyage_id, stage="calculating", extraction=extraction)
    laytime, dispute = await asyncio.gather(...)
    await store.patch(voyage_id, stage="drafting", laytime=laytime, dispute=dispute)
    packet = await drafter.run(...)
    await store.patch(voyage_id, stage="done", packet=packet)

`patch` is a partial update that merges field-by-field onto the stored model
without reading-then-writing in the caller (which would race other tasks).
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol, runtime_checkable

from .schemas import VesselSummary, VoyageState, VoyageSummary


@runtime_checkable
class VoyageStore(Protocol):
    """Async storage contract for voyage state."""

    async def save(self, state: VoyageState) -> None: ...

    async def load(self, voyage_id: str) -> VoyageState | None: ...

    async def patch(self, voyage_id: str, /, **fields: Any) -> VoyageState | None: ...

    async def delete(self, voyage_id: str) -> bool: ...

    async def list(self) -> list[VoyageSummary]: ...

    async def list_vessels(self) -> list[VesselSummary]: ...


class InMemoryStore:
    """In-process dict implementation of ``VoyageStore``.

    A single asyncio.Lock serialises mutating ops so concurrent ``patch`` /
    ``save`` calls do not interleave field updates. Reads are lock-free; they
    see a consistent VoyageState because Pydantic models are immutable enough
    for our purposes (each mutation creates a new instance).
    """

    def __init__(self) -> None:
        self._voyages: dict[str, VoyageState] = {}
        self._lock = asyncio.Lock()

    async def save(self, state: VoyageState) -> None:
        async with self._lock:
            self._voyages[state.voyage_id] = state

    async def load(self, voyage_id: str) -> VoyageState | None:
        return self._voyages.get(voyage_id)

    async def patch(self, voyage_id: str, /, **fields: Any) -> VoyageState | None:
        """Merge ``fields`` onto the stored VoyageState; return the new state.

        Returns ``None`` (and does nothing) if ``voyage_id`` is unknown.
        """
        async with self._lock:
            existing = self._voyages.get(voyage_id)
            if existing is None:
                return None
            updated = existing.model_copy(update=fields)
            self._voyages[voyage_id] = updated
            return updated

    async def delete(self, voyage_id: str) -> bool:
        """Remove a voyage by id. Returns True if it existed, False otherwise."""
        async with self._lock:
            return self._voyages.pop(voyage_id, None) is not None

    async def list(self) -> list[VoyageSummary]:
        """Return all voyages as summaries, newest-first by ``created_at``."""
        states = sorted(
            self._voyages.values(), key=lambda s: s.created_at, reverse=True
        )
        return [VoyageSummary.from_state(s) for s in states]

    async def list_vessels(self) -> list[VesselSummary]:
        """Group voyages by ``vessel_name`` into vessel aggregates, newest-first.

        Voyages still being processed (no extraction yet, so no vessel_name) are
        skipped — a voyage only gains a vessel identity once Agent 1 names it.
        Vessels are ordered by ``last_activity`` (the newest voyage in the group),
        which falls out for free from iterating the already newest-first summaries.
        """
        summaries = await self.list()  # newest-first
        groups: dict[str, list[VoyageSummary]] = {}
        for s in summaries:
            if s.vessel_name is None:
                continue
            groups.setdefault(s.vessel_name, []).append(s)

        vessels: list[VesselSummary] = []
        for name, rows in groups.items():
            quantums = [r.quantum_eur for r in rows if r.quantum_eur is not None]
            newest = rows[0]  # rows inherit the newest-first ordering of summaries
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
