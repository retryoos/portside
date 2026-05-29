"""Tests for ``SqlVoyageStore`` — the relational persistence layer.

Pure (no Anthropic SDK, no network); each test gets its own temp-file SQLite DB
via ``tmp_path`` and uses ``asyncio.run`` so we don't need ``pytest-asyncio``.
The headline guarantees: the full VoyageState tree round-trips byte-identical
(which also guards the EUR 84,375.00 gate), and state survives a "restart"
(a fresh engine + store on the same file).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from portside_api.db.engine import create_all, make_engine, make_sessionmaker
from portside_api.fixtures import demo_voyage_fixture, seed_voyages
from portside_api.schemas import VoyageState
from portside_api.storage import SqlVoyageStore


def _url(tmp_path: Path, name: str = "t.db") -> str:
    return f"sqlite+aiosqlite:///{tmp_path / name}"


async def _fresh_store(url: str) -> tuple[object, SqlVoyageStore]:
    engine = make_engine(url)
    await create_all(engine)
    return engine, SqlVoyageStore(make_sessionmaker(engine))


def test_full_tree_round_trip_is_exact(tmp_path: Path) -> None:
    """save -> load returns a VoyageState equal to the original, gate intact."""

    async def go() -> tuple[VoyageState, VoyageState | None]:
        engine, store = await _fresh_store(_url(tmp_path))
        original = demo_voyage_fixture("v_round_trip")
        await store.save(original)
        loaded = await store.load("v_round_trip")
        await engine.dispose()
        return original, loaded

    original, loaded = asyncio.run(go())
    assert loaded is not None
    assert loaded == original
    # The gate: the demurrage figure must survive persistence untouched.
    assert loaded.laytime is not None
    assert loaded.laytime.demurrage_due_eur == 84375.0


def test_minimal_state_round_trip(tmp_path: Path) -> None:
    """A voyage with no extraction/laytime/dispute/packet round-trips too."""

    async def go() -> tuple[VoyageState, VoyageState | None]:
        engine, store = await _fresh_store(_url(tmp_path))
        original = VoyageState(
            voyage_id="v_min", perspective="owner", stage="uploaded"
        )
        await store.save(original)
        loaded = await store.load("v_min")
        await engine.dispose()
        return original, loaded

    original, loaded = asyncio.run(go())
    assert loaded == original


def test_persists_across_restart(tmp_path: Path) -> None:
    """A fresh engine + store on the same DB file still sees prior data."""
    url = _url(tmp_path, "restart.db")

    async def write() -> None:
        engine, store = await _fresh_store(url)
        await store.save(demo_voyage_fixture("v_persist"))
        await engine.dispose()

    async def read() -> VoyageState | None:
        engine = make_engine(url)  # no create_all — schema already on disk
        store = SqlVoyageStore(make_sessionmaker(engine))
        loaded = await store.load("v_persist")
        await engine.dispose()
        return loaded

    asyncio.run(write())
    loaded = asyncio.run(read())
    assert loaded is not None
    assert loaded.voyage_id == "v_persist"
    assert loaded.laytime is not None
    assert loaded.laytime.demurrage_due_eur == 84375.0


def test_load_missing_returns_none(tmp_path: Path) -> None:
    async def go() -> VoyageState | None:
        engine, store = await _fresh_store(_url(tmp_path))
        result = await store.load("v_nope")
        await engine.dispose()
        return result

    assert asyncio.run(go()) is None


def test_patch_merges_scalar_and_subtree(tmp_path: Path) -> None:
    async def go() -> tuple[VoyageState | None, VoyageState | None, VoyageState | None]:
        engine, store = await _fresh_store(_url(tmp_path))
        await store.save(
            VoyageState(voyage_id="v_p", perspective="owner", stage="uploaded")
        )
        # scalar field merge
        patched = await store.patch("v_p", stage="extracting")
        # subtree merge: attach a full extraction in one patch
        ext = demo_voyage_fixture().extraction
        await store.patch("v_p", stage="calculating", extraction=ext)
        reloaded = await store.load("v_p")
        missing = await store.patch("v_unknown", stage="done")
        await engine.dispose()
        return patched, reloaded, missing

    patched, reloaded, missing = asyncio.run(go())
    assert patched is not None and patched.stage == "extracting"
    assert reloaded is not None and reloaded.stage == "calculating"
    assert reloaded.extraction == demo_voyage_fixture().extraction
    assert missing is None


def test_list_ordering_and_vessel_grouping(tmp_path: Path) -> None:
    async def go() -> tuple[list, list]:
        engine, store = await _fresh_store(_url(tmp_path))
        for state in seed_voyages():
            await store.save(state)
        summaries = await store.list()
        vessels = await store.list_vessels()
        await engine.dispose()
        return summaries, vessels

    summaries, vessels = asyncio.run(go())

    assert len(summaries) == 10  # 3 + 4 + 2 + 1
    # newest-first by created_at
    times = [s.created_at for s in summaries]
    assert times == sorted(times, reverse=True)

    counts = {v.name: v.voyage_count for v in vessels}
    assert counts == {
        "MT Aegean Pioneer": 3,
        "MT Ionian Star": 4,
        "MT Baltic Trader": 2,
        "MT Levant Carrier": 1,
    }
