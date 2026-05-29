"""A7 tests — the research tool, the evidence gatherer, and the endpoint.

All offline: the weather tool serves a committed fixture, and the researcher
deterministically maps weather-stoppage events to that fixture, so every
expectation here is reproducible without an API key or network.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from portside_api import main as main_mod
from portside_api.agents.tools import get_weather
from portside_api.db.engine import create_all, make_engine, make_sessionmaker
from portside_api.fixtures import demo_voyage_fixture
from portside_api.objects import LocalObjectStore
from portside_api.researcher import EvidenceItem, gather_evidence
from portside_api.storage import InMemoryStore, SqlVoyageStore


def test_get_weather_fixture_for_rotterdam() -> None:
    obs = asyncio.run(get_weather("Rotterdam", "2026-05-17"))
    assert obs is not None
    assert obs.precipitation_mm_per_hr == 0.2
    assert obs.source.startswith("Rotterdam Port Authority")


def test_get_weather_unknown_is_none() -> None:
    assert asyncio.run(get_weather("Nowhere", "1999-01-01")) is None


def test_gather_evidence_supports_owner_on_demo() -> None:
    voyage = demo_voyage_fixture()
    assert voyage.extraction is not None and voyage.dispute is not None
    bundle = asyncio.run(gather_evidence(voyage.extraction, voyage.dispute))
    assert len(bundle.items) == 1
    item = bundle.items[0]
    assert item.event_id == "e6"
    assert item.supports == "owner"  # 0.2 mm/hr < 0.5 mm/hr threshold
    assert "0.2 mm/hr" in item.observed_value
    assert "Rotterdam" in item.summary


def test_evidence_persists_through_sql_store(tmp_path: Path) -> None:
    """list_evidence on Sql round-trips items recorded via record_evidence."""

    async def go() -> list[EvidenceItem]:
        engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'e.db'}")
        await create_all(engine)
        store = SqlVoyageStore(make_sessionmaker(engine))
        from portside_api.schemas import VoyageState

        await store.save(
            VoyageState(voyage_id="v_e", perspective="owner", stage="done")
        )
        voyage = demo_voyage_fixture()
        assert voyage.extraction is not None and voyage.dispute is not None
        bundle = await gather_evidence(voyage.extraction, voyage.dispute)
        await store.record_evidence("v_e", bundle.items)
        out = await store.list_evidence("v_e")
        await engine.dispose()
        return out

    items = asyncio.run(go())
    assert [i.event_id for i in items] == ["e6"]
    assert items[0].supports == "owner"


@pytest.fixture
def client(tmp_path: object) -> Iterator[TestClient]:
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(main_mod, "store", InMemoryStore())
        mp.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))  # type: ignore[arg-type]
        with TestClient(main_mod.app) as c:
            yield c


def test_evidence_endpoint_lazy_gather_and_cache(client: TestClient) -> None:
    vid = "v_aegean_pioneer"  # seeded, dev-user owned, full demo voyage
    first = client.get(f"/voyages/{vid}/evidence")
    assert first.status_code == 200, first.text
    items = first.json()
    assert [i["event_id"] for i in items] == ["e6"]
    assert items[0]["supports"] == "owner"

    # Second call should return the same cached items (no re-gather).
    second = client.get(f"/voyages/{vid}/evidence")
    assert second.json() == items


def test_evidence_endpoint_409_when_not_ready(client: TestClient) -> None:
    from portside_api.schemas import VoyageState

    async def _seed() -> None:
        await main_mod.store.save(
            VoyageState(voyage_id="v_raw", perspective="owner", stage="uploaded")
        )

    asyncio.run(_seed())
    resp = client.get("/voyages/v_raw/evidence")
    assert resp.status_code == 409
