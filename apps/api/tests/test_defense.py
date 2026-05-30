"""A6 tests — the charterer rebuttal gate.

The deterministic core (swing math, points, template letter) is exercised here
without an API key. The endpoint test stubs ``defense.draft_rebuttal_letter`` so
no Anthropic call is made even if a key is present in the environment.

Hard locked: winning the contested 4h weather stoppage on the Rotterdam demo
drops the quantum from EUR 84,375.00 to EUR 76,875.00.
"""

from __future__ import annotations

import asyncio
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from portside_api import defense, main as main_mod
from portside_api.defense import (
    RebuttalPoint,
    build_rebuttal_points,
    recompute_after_concessions,
    won_event_ids,
    _template_letter,
)
from portside_api.fixtures import demo_voyage_fixture
from portside_api.objects import LocalObjectStore
from portside_api.storage import InMemoryStore


def test_won_event_ids_on_demo_is_just_the_weather_stoppage() -> None:
    laytime = demo_voyage_fixture().laytime
    assert laytime is not None
    assert won_event_ids(laytime) == ["e6"]


def test_recompute_after_concessions_locks_76875() -> None:
    laytime = demo_voyage_fixture().laytime
    assert laytime is not None
    reduced, conceded, contested = recompute_after_concessions(laytime, ["e6"])
    assert contested == 7500.0  # 4h * 1875
    assert reduced == 76875.0
    assert conceded == 76875.0  # equals reduced by definition


def test_recompute_with_no_concessions_keeps_original() -> None:
    laytime = demo_voyage_fixture().laytime
    assert laytime is not None
    reduced, conceded, contested = recompute_after_concessions(laytime, [])
    assert contested == 0.0
    assert reduced == 84375.0
    assert conceded == 84375.0


def test_build_rebuttal_points_on_demo() -> None:
    voyage = demo_voyage_fixture()
    assert voyage.laytime is not None and voyage.dispute is not None
    points = build_rebuttal_points(voyage.laytime, voyage.dispute)
    assert len(points) == 1
    p = points[0]
    assert p.event_id == "e6"
    assert p.swing_eur == 7500.0
    assert "CP clause 14" in p.clause_cited


def test_template_letter_quotes_locked_figures() -> None:
    voyage = demo_voyage_fixture()
    assert voyage.extraction is not None
    points = [
        RebuttalPoint(
            event_id="e6",
            owner_claim="x",
            charterer_response="y",
            clause_cited="CP clause 14",
            swing_eur=7500.0,
        )
    ]
    letter = _template_letter(voyage.extraction, 84375.0, 76875.0, 7500.0, points)
    assert "EUR 84,375.00" in letter
    assert "EUR 76,875.00" in letter
    assert "EUR 7,500.00" in letter


@pytest.fixture
def client(tmp_path: object) -> Iterator[TestClient]:
    async def _stub_letter(*_args: object, **_kwargs: object) -> str:
        return "STUB REBUTTAL"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(main_mod, "store", InMemoryStore())
        mp.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))  # type: ignore[arg-type]
        # Avoid any Anthropic call from the route, even if a key is in env.
        mp.setattr(defense, "draft_rebuttal_letter", _stub_letter)
        with TestClient(main_mod.app) as c:
            yield c


def test_rebut_endpoint_returns_locked_swing(client: TestClient) -> None:
    resp = client.post("/voyages/v_aegean_pioneer/rebut")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["original_quantum_eur"] == 84375.0
    assert body["reduced_quantum_eur"] == 76875.0
    assert body["contested_eur"] == 7500.0
    assert body["conceded_eur"] == 76875.0
    assert body["rebuttal_letter_markdown"] == "STUB REBUTTAL"
    assert [p["event_id"] for p in body["points"]] == ["e6"]


def test_rebut_endpoint_409_when_not_ready(client: TestClient) -> None:
    # Seed an upload-stage voyage with no analysis tree yet.
    from portside_api.schemas import VoyageState

    async def _seed() -> None:
        await main_mod.store.save(
            VoyageState(voyage_id="v_partial", perspective="owner", stage="uploaded")
        )

    asyncio.run(_seed())
    resp = client.post("/voyages/v_partial/rebut")
    assert resp.status_code == 409
