"""Voyage state storage.

Hackathon-grade: a single in-process dict keyed by voyage_id. No persistence —
restarting the process clears all state, which is acceptable for the demo. The
``VoyageStore`` Protocol leaves room to swap in a real backend later without
touching call sites.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .schemas import VoyageState


@runtime_checkable
class VoyageStore(Protocol):
    """Async storage contract for voyage state."""

    async def save(self, state: VoyageState) -> None: ...

    async def load(self, voyage_id: str) -> VoyageState | None: ...


class InMemoryStore:
    """In-process dict implementation of ``VoyageStore``."""

    def __init__(self) -> None:
        self._voyages: dict[str, VoyageState] = {}

    async def save(self, state: VoyageState) -> None:
        self._voyages[state.voyage_id] = state

    async def load(self, voyage_id: str) -> VoyageState | None:
        return self._voyages.get(voyage_id)
