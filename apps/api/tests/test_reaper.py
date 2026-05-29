"""Tests for A4 interrupted-run recovery (``reap_stale_processing``).

A real upload left mid-pipeline (non-terminal stage, has documents) past the
staleness threshold is reaped to "error"; fresh runs, terminal voyages, and the
document-less demo seeds are left alone. A negative threshold makes the cutoff
slightly in the future so "currently stale" rows match deterministically.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from portside_api.db.engine import create_all, make_engine, make_sessionmaker
from portside_api.objects import StoredDocument
from portside_api.schemas import VoyageState
from portside_api.storage import SqlVoyageStore


def _doc(role: str = "cp") -> StoredDocument:
    return StoredDocument(
        role=role,
        object_key=f"voyages/x/{role}.pdf",
        content_type="application/pdf",
        size_bytes=10,
    )


async def _store(tmp_path: Path, name: str) -> tuple[object, SqlVoyageStore]:
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / name}")
    await create_all(engine)
    return engine, SqlVoyageStore(make_sessionmaker(engine))


def test_reaps_interrupted_upload(tmp_path: Path) -> None:
    async def go() -> tuple[int, VoyageState | None]:
        engine, store = await _store(tmp_path, "a.db")
        await store.save(
            VoyageState(voyage_id="v_x", perspective="owner", stage="extracting")
        )
        await store.record_documents("v_x", [_doc()])
        reaped = await store.reap_stale_processing(older_than_seconds=-10)
        state = await store.load("v_x")
        await engine.dispose()
        return reaped, state

    reaped, state = asyncio.run(go())
    assert reaped == 1
    assert state is not None and state.stage == "error"
    assert state.error == "processing interrupted"


def test_does_not_reap_without_documents(tmp_path: Path) -> None:
    """Demo seeds carry processing-like stages but no uploaded documents."""

    async def go() -> tuple[int, VoyageState | None]:
        engine, store = await _store(tmp_path, "b.db")
        await store.save(
            VoyageState(voyage_id="v_seed", perspective="owner", stage="drafting")
        )
        reaped = await store.reap_stale_processing(older_than_seconds=-10)
        state = await store.load("v_seed")
        await engine.dispose()
        return reaped, state

    reaped, state = asyncio.run(go())
    assert reaped == 0
    assert state is not None and state.stage == "drafting"


def test_does_not_reap_fresh_run(tmp_path: Path) -> None:
    async def go() -> tuple[int, VoyageState | None]:
        engine, store = await _store(tmp_path, "c.db")
        await store.save(
            VoyageState(voyage_id="v_fresh", perspective="owner", stage="extracting")
        )
        await store.record_documents("v_fresh", [_doc()])
        # Large threshold: a row updated just now is not yet stale.
        reaped = await store.reap_stale_processing(older_than_seconds=3600)
        state = await store.load("v_fresh")
        await engine.dispose()
        return reaped, state

    reaped, state = asyncio.run(go())
    assert reaped == 0
    assert state is not None and state.stage == "extracting"


def test_does_not_reap_terminal_voyage(tmp_path: Path) -> None:
    async def go() -> tuple[int, VoyageState | None]:
        engine, store = await _store(tmp_path, "d.db")
        await store.save(
            VoyageState(voyage_id="v_done", perspective="owner", stage="done")
        )
        await store.record_documents("v_done", [_doc()])
        reaped = await store.reap_stale_processing(older_than_seconds=-10)
        state = await store.load("v_done")
        await engine.dispose()
        return reaped, state

    reaped, state = asyncio.run(go())
    assert reaped == 0
    assert state is not None and state.stage == "done"
