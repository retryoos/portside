"""Safety-validation gate for the inline-revise micro-agent.

These run without an API key: they exercise the pure validator and the
manual-edit path of ``revise`` (which never calls the model). A claim letter
where a re-word silently changed a dollar amount, a clause number, or an event
ID would be a catastrophic legal failure — these tests lock that door.
"""

from __future__ import annotations

import asyncio

from portside_api.fixtures import demo_voyage_fixture
from portside_api.reviser import (
    ReviseRequest,
    ReviseSegment,
    revise,
    validate_revision,
)

ORIGINAL = (
    "Per CP clause 14, the weather stoppage at e6 does not meet the threshold, "
    "so demurrage of EUR 84,375.00 is due."
)


def test_clean_reword_passes():
    revised = (
        "The weather stoppage at e6 fails the CP clause 14 threshold; "
        "accordingly EUR 84,375.00 in demurrage is due."
    )
    ok, report = validate_revision(ORIGINAL, revised)
    assert ok is True
    assert report.quantum_unchanged is True
    assert "14" in report.clauses_preserved
    assert "e6" in report.events_preserved


def test_changed_monetary_value_is_rejected():
    tampered = ORIGINAL.replace("84,375.00", "90,000.00")
    ok, report = validate_revision(ORIGINAL, tampered)
    assert ok is False
    assert report.quantum_unchanged is False


def test_dropped_clause_is_rejected():
    no_clause = "The weather stoppage at e6 fails; EUR 84,375.00 is due."
    ok, report = validate_revision(ORIGINAL, no_clause)
    assert ok is False
    assert any("clause" in w for w in report.warnings)


def test_dropped_event_is_rejected():
    no_event = "Per CP clause 14, the stoppage fails; EUR 84,375.00 is due."
    ok, report = validate_revision(ORIGINAL, no_event)
    assert ok is False
    assert any("event" in w for w in report.warnings)


def _manual_request(new_text: str) -> ReviseRequest:
    return ReviseRequest(
        surface="letter",
        segment_ids=["letter-para-3"],
        instruction="manual edit",
        mode="manual",
        manual_text=new_text,
        segments=[ReviseSegment(id="letter-para-3", text=ORIGINAL)],
    )


def test_manual_edit_safe_change_is_applied():
    voyage = demo_voyage_fixture()
    safe = (
        "The weather stoppage at e6 fails the CP clause 14 threshold; "
        "EUR 84,375.00 in demurrage is due."
    )
    blocked, response = asyncio.run(revise(_manual_request(safe), voyage))
    assert blocked is False
    assert response.segments[0].text == safe


def test_manual_edit_changing_quantum_is_blocked():
    voyage = demo_voyage_fixture()
    tampered = ORIGINAL.replace("84,375.00", "1.00")
    blocked, response = asyncio.run(revise(_manual_request(tampered), voyage))
    assert blocked is True
    # rejected -> the original text is preserved, not the tampered text.
    assert response.segments[0].text == ORIGINAL
