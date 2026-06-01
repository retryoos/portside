"""Route-level tests for ``GET /voyages/{id}/citations`` (W5).

The deterministic picker harness has unit coverage in
``test_analyst_citations.py``. These tests pin the wire surface the W5
frontend consumes:

- 404 on unknown voyage
- 409 when no dispute is on the state yet
- 200 with one bundle per flagged event whose picker survived verification
- A faked-failure picker (raises) downgrades to ``[]`` and does NOT 5xx
- Cache is read-through: a second hit serves the persisted rows without
  re-running the picker
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from laytimely_api import main as main_mod  # noqa: E402
from laytimely_api.agents import analyst  # noqa: E402
from laytimely_api.fixtures import demo_voyage_fixture  # noqa: E402
from laytimely_api.legal.models import CitedAuthority  # noqa: E402
from laytimely_api.objects import LocalObjectStore  # noqa: E402
from laytimely_api.schemas import VoyageState  # noqa: E402
from laytimely_api.storage import InMemoryStore  # noqa: E402


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


def _stub_picker_returns(
    monkeypatch: pytest.MonkeyPatch, picks_per_event: dict[str, list[CitedAuthority]]
) -> None:
    """Replace the per-event picker with a deterministic stub keyed by event_id."""

    async def fake(event):  # type: ignore[no-untyped-def]
        return list(picks_per_event.get(event.event_id, []))

    monkeypatch.setattr(analyst, "_citations_for_event", fake)


def test_citations_404_when_unknown(client: TestClient) -> None:
    assert client.get("/voyages/v_missing/citations").status_code == 404


def test_citations_409_when_no_dispute(client: TestClient) -> None:
    async def _seed() -> None:
        await main_mod.store.save(
            VoyageState(voyage_id="v_partial", perspective="owner", stage="uploaded")
        )

    asyncio.run(_seed())
    assert client.get("/voyages/v_partial/citations").status_code == 409


def test_citations_returns_bundle_for_picked_event(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _seed_demo()
    assert state.dispute is not None
    event_id = state.dispute.flagged_events[0].event_id
    _stub_picker_returns(
        monkeypatch,
        {
            event_id: [
                CitedAuthority(
                    citation="The Mexico 1 [1990] 1 Lloyd's Rep 507",
                    verified_via_tool=True,
                    tool_used="corpus",
                    proposition="weather exception requires express threshold",
                )
            ]
        },
    )

    resp = client.get("/voyages/v_aegean_pioneer/citations")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    bundle = body[0]
    assert bundle["event_id"] == event_id
    assert [a["citation"] for a in bundle["cited_authorities"]] == [
        "The Mexico 1 [1990] 1 Lloyd's Rep 507"
    ]


def test_citations_picker_exception_downgrades_to_empty_not_500(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_demo()

    async def fake(event):  # type: ignore[no-untyped-def]
        raise RuntimeError("simulated picker failure")

    monkeypatch.setattr(analyst, "_citations_for_event", fake)

    resp = client.get("/voyages/v_aegean_pioneer/citations")
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_citations_cache_is_read_through(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _seed_demo()
    assert state.dispute is not None
    event_id = state.dispute.flagged_events[0].event_id

    call_count = {"n": 0}

    async def fake(event):  # type: ignore[no-untyped-def]
        call_count["n"] += 1
        return [
            CitedAuthority(
                citation="The Mexico 1 [1990] 1 Lloyd's Rep 507",
                verified_via_tool=True,
                tool_used="corpus",
                proposition="real authority",
            )
        ]

    monkeypatch.setattr(analyst, "_citations_for_event", fake)

    first = client.get("/voyages/v_aegean_pioneer/citations")
    second = client.get("/voyages/v_aegean_pioneer/citations")
    assert first.status_code == 200 and second.status_code == 200
    assert first.json() == second.json()
    # First call hit the picker once per flagged event; the second call must
    # serve from the cache without invoking the picker again.
    expected_first_pass = len(state.dispute.flagged_events)
    assert call_count["n"] == expected_first_pass
