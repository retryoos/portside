"""Tests for ``InMemoryStore`` — save/load round-trip + the new patch contract.

These tests are pure (no Anthropic SDK, no network). They use ``asyncio.run``
so we don't need ``pytest-asyncio`` as a dev dependency.
"""

from __future__ import annotations

import asyncio

from laytimely_api.fixtures import demo_voyage_fixture
from laytimely_api.schemas import VoyageState
from laytimely_api.storage import InMemoryStore


def _minimal_state(
    voyage_id: str = "v_test_0001",
    stage: str = "uploaded",
) -> VoyageState:
    return VoyageState(voyage_id=voyage_id, perspective="owner", stage=stage)


def test_save_then_load_round_trip() -> None:
    store = InMemoryStore()
    state = demo_voyage_fixture(voyage_id="v_round_trip")

    async def go() -> VoyageState | None:
        await store.save(state)
        return await store.load("v_round_trip")

    loaded = asyncio.run(go())
    assert loaded is not None
    assert loaded == state
    assert loaded.voyage_id == "v_round_trip"
    assert loaded.stage == "done"


def test_load_missing_returns_none() -> None:
    store = InMemoryStore()

    async def go() -> VoyageState | None:
        return await store.load("v_does_not_exist")

    assert asyncio.run(go()) is None


def test_patch_missing_returns_none_and_noop() -> None:
    store = InMemoryStore()

    async def go() -> tuple[VoyageState | None, VoyageState | None]:
        result = await store.patch("v_unknown", stage="extracting")
        after = await store.load("v_unknown")
        return result, after

    result, after = asyncio.run(go())
    assert result is None
    assert after is None


def test_patch_updates_single_field() -> None:
    store = InMemoryStore()
    seed = _minimal_state(stage="uploaded")

    async def go() -> VoyageState | None:
        await store.save(seed)
        await store.patch(seed.voyage_id, stage="extracting")
        return await store.load(seed.voyage_id)

    loaded = asyncio.run(go())
    assert loaded is not None
    assert loaded.stage == "extracting"
    assert loaded.voyage_id == seed.voyage_id
    assert loaded.perspective == "owner"
    assert loaded.error is None
    assert loaded.extraction is None


def test_patch_updates_multiple_fields() -> None:
    store = InMemoryStore()
    demo = demo_voyage_fixture(voyage_id="v_multi")
    seed = _minimal_state(voyage_id="v_multi", stage="uploaded")
    assert demo.extraction is not None
    extraction = demo.extraction

    async def go() -> VoyageState | None:
        await store.save(seed)
        await store.patch("v_multi", stage="done", extraction=extraction)
        return await store.load("v_multi")

    loaded = asyncio.run(go())
    assert loaded is not None
    assert loaded.stage == "done"
    assert loaded.extraction == extraction


def test_concurrent_patches_serialise() -> None:
    """Fire 20 patches concurrently; assert no corruption and the lock works."""
    store = InMemoryStore()
    seed = _minimal_state(voyage_id="v_race", stage="uploaded")

    async def go() -> VoyageState | None:
        await store.save(seed)
        await asyncio.gather(
            *(
                store.patch("v_race", stage="extracting", error=str(i))
                for i in range(20)
            )
        )
        return await store.load("v_race")

    loaded = asyncio.run(go())
    assert loaded is not None
    assert loaded.stage == "extracting"
    assert loaded.error is not None
    # Final error must be one of the 20 patches — never garbage / corrupted.
    assert loaded.error in {str(i) for i in range(20)}


def test_patch_returns_updated_state() -> None:
    store = InMemoryStore()
    seed = _minimal_state(voyage_id="v_return", stage="uploaded")

    async def go() -> VoyageState | None:
        await store.save(seed)
        return await store.patch("v_return", stage="calculating")

    returned = asyncio.run(go())
    assert returned is not None
    assert returned.voyage_id == "v_return"
    assert returned.stage == "calculating"
    assert returned.perspective == "owner"
