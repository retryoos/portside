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

from .schemas import VoyageState


@runtime_checkable
class VoyageStore(Protocol):
    """Async storage contract for voyage state."""

    async def save(self, state: VoyageState) -> None: ...

    async def load(self, voyage_id: str) -> VoyageState | None: ...

    async def patch(self, voyage_id: str, /, **fields: Any) -> VoyageState | None: ...


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
