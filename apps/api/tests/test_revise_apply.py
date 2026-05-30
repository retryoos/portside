"""Tests for A5 — persisting accepted inline revisions into the stored packet.

Covers the pure ``apply_revisions`` helper (safety gate + substitution) and the
``POST /voyages/{id}/revise/apply`` endpoint (persist + reload), all without an
API key. The gate must block any edit that changes a monetary value, so the
EUR 84,375.00 figure can never be silently rewritten into the store.
"""

from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from portside_api import main as main_mod
from portside_api.fixtures import demo_voyage_fixture
from portside_api.objects import LocalObjectStore
from portside_api.reviser import RevisionEdit, apply_revisions
from portside_api.storage import InMemoryStore

# A reword of a packet sentence with no EUR/clause/event tokens — always safe.
_SAFE_FROM = "All rights reserved."
_SAFE_TO = "All rights are expressly reserved."


def test_apply_revisions_applies_safe_edit() -> None:
    packet = demo_voyage_fixture().packet
    assert packet is not None
    new_packet, report, error = apply_revisions(
        packet, "letter", [RevisionEdit(original=_SAFE_FROM, revised=_SAFE_TO)]
    )
    assert error is None
    assert new_packet is not None
    assert _SAFE_TO in new_packet.claim_letter_markdown
    assert _SAFE_FROM not in new_packet.claim_letter_markdown
    assert new_packet.quantum_eur == packet.quantum_eur  # money untouched


def test_apply_revisions_blocks_monetary_change() -> None:
    packet = demo_voyage_fixture().packet
    assert packet is not None
    new_packet, report, error = apply_revisions(
        packet,
        "letter",
        [
            RevisionEdit(
                original="Demurrage due: EUR 84,375.00",
                revised="Demurrage due: EUR 90,000.00",
            )
        ],
    )
    assert new_packet is None  # blocked by the safety gate
    assert error is None
    assert report.warnings  # explains why


def test_apply_revisions_reports_missing_segment() -> None:
    packet = demo_voyage_fixture().packet
    assert packet is not None
    new_packet, _report, error = apply_revisions(
        packet, "letter", [RevisionEdit(original="not in this letter zzz", revised="x")]
    )
    assert new_packet is None
    assert error is not None


@pytest.fixture
def client(tmp_path: object) -> Iterator[TestClient]:
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(main_mod, "store", InMemoryStore())
        mp.setattr(main_mod, "object_store", LocalObjectStore(tmp_path))  # type: ignore[arg-type]
        with TestClient(main_mod.app) as c:
            yield c


def test_apply_endpoint_persists_and_blocks(client: TestClient) -> None:
    vid = "v_aegean_pioneer"  # seeded, owned by the dev user, has a packet

    # Safe edit persists and is visible on reload.
    ok = client.post(
        f"/voyages/{vid}/revise/apply",
        json={"surface": "letter", "edits": [{"original": _SAFE_FROM, "revised": _SAFE_TO}]},
    )
    assert ok.status_code == 200, ok.text
    assert _SAFE_TO in ok.json()["packet"]["claim_letter_markdown"]
    reloaded = client.get(f"/voyages/{vid}").json()
    assert _SAFE_TO in reloaded["packet"]["claim_letter_markdown"]

    # A monetary change is rejected and does not reach the store.
    blocked = client.post(
        f"/voyages/{vid}/revise/apply",
        json={
            "surface": "letter",
            "edits": [
                {
                    "original": "Demurrage due: EUR 84,375.00",
                    "revised": "Demurrage due: EUR 90,000.00",
                }
            ],
        },
    )
    assert blocked.status_code == 422
    after = client.get(f"/voyages/{vid}").json()
    assert "EUR 84,375.00" in after["packet"]["claim_letter_markdown"]
