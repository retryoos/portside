"""Route-level tests for ``GET /voyages/{id}/strengths`` (W4).

The deterministic ``build_panels`` helpers have unit coverage in
``test_evidence_and_strength.py``. These pin the route contract the W4
frontend depends on:

- 404 on unknown voyage
- 409 when no dispute is on the state yet
- 200 returns one panel per flagged event, each with the four named
  sub-scores; ``time_bar_risk`` reflects the deterministic mapping over
  ``packet.days_until_time_bar``
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Iterator, get_args

import pytest
from fastapi.testclient import TestClient

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from portside_api import main as main_mod  # noqa: E402
from portside_api.claim_strength import Strength  # noqa: E402
from portside_api.fixtures import demo_voyage_fixture  # noqa: E402
from portside_api.objects import LocalObjectStore  # noqa: E402
from portside_api.schemas import VoyageState  # noqa: E402
from portside_api.storage import InMemoryStore  # noqa: E402


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(main_mod, "store", InMemoryStore())
        mp.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))
        with TestClient(main_mod.app) as c:
            yield c


def _seed_demo(voyage_id: str = "v_aegean_pioneer") -> VoyageState:
    state = demo_voyage_fixture(voyage_id, "owner")

    async def _save() -> None:
        await main_mod.store.save(state)

    asyncio.run(_save())
    return state


def test_strengths_404_when_unknown(client: TestClient) -> None:
    assert client.get("/voyages/v_missing/strengths").status_code == 404


def test_strengths_409_when_no_dispute(client: TestClient) -> None:
    async def _seed() -> None:
        await main_mod.store.save(
            VoyageState(voyage_id="v_partial", perspective="owner", stage="uploaded")
        )

    asyncio.run(_seed())
    assert client.get("/voyages/v_partial/strengths").status_code == 409


def test_strengths_returns_one_panel_per_flagged_event(
    client: TestClient,
) -> None:
    state = _seed_demo()
    assert state.dispute is not None
    resp = client.get("/voyages/v_aegean_pioneer/strengths")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    event_ids_in_body = {row["event_id"] for row in body}
    assert event_ids_in_body == {
        fe.event_id for fe in state.dispute.flagged_events
    }


def test_strengths_sub_scores_use_closed_vocabulary(
    client: TestClient,
) -> None:
    _seed_demo()
    resp = client.get("/voyages/v_aegean_pioneer/strengths")
    assert resp.status_code == 200
    allowed = set(get_args(Strength))
    for row in resp.json():
        sub = row["sub_scores"]
        assert sub["clause_clarity"] in allowed
        assert sub["evidence_completeness"] in allowed
        assert sub["counterparty_pushback_risk"] in allowed
        assert sub["time_bar_risk"] in allowed


def test_strengths_time_bar_risk_matches_days_until_time_bar(
    client: TestClient,
) -> None:
    state = _seed_demo()
    assert state.packet is not None
    days = state.packet.days_until_time_bar
    expected: Strength
    if days > 45:
        expected = "Strong"
    elif days > 14:
        expected = "Arguable"
    else:
        expected = "Weak"

    resp = client.get("/voyages/v_aegean_pioneer/strengths")
    assert resp.status_code == 200
    for row in resp.json():
        assert row["sub_scores"]["time_bar_risk"] == expected


def test_strengths_clause_clarity_reflects_owner_position(
    client: TestClient,
) -> None:
    """The v0.1 deterministic mapping turns the analyst's calibrated
    ``owner_position_strength`` into a (clarity, pushback) pair. The demo
    fixture pins strength=0.8 on the weather event, which lands in the
    Strong/Weak bucket."""
    state = _seed_demo()
    assert state.dispute is not None
    strong_event_ids = {
        fe.event_id
        for fe in state.dispute.flagged_events
        if fe.owner_position_strength >= 0.7
    }
    resp = client.get("/voyages/v_aegean_pioneer/strengths")
    by_id = {row["event_id"]: row["sub_scores"] for row in resp.json()}
    for event_id in strong_event_ids:
        assert by_id[event_id]["clause_clarity"] == "Strong"
        assert by_id[event_id]["counterparty_pushback_risk"] == "Weak"
