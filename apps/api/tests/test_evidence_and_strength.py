"""Tests for evidence checklist (§1.4) and claim strength sub-scores (§1.5).

The contract under test: ``attached`` and ``evidence_completeness`` and
``time_bar_risk`` are deterministic; the model never owns them. Run against
the Rotterdam fixture so the integration is meaningful.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from laytimely_api.claim_strength import (  # noqa: E402
    build_panels,
    evidence_completeness_from_checklist,
    time_bar_risk,
)
from laytimely_api.evidence_checklist import (  # noqa: E402
    EvidenceChecklist,
    EvidenceItem,
    build_checklist,
)
from laytimely_api.fixtures import demo_voyage_fixture  # noqa: E402
from laytimely_api.researcher import EvidenceBundle, EvidenceItem as ResearchEvidence  # noqa: E402


# ---------------------------------------------------------------------------
# Evidence checklist
# ---------------------------------------------------------------------------


def test_checklist_pairs_each_evidence_required_line_with_a_role() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    assert state.dispute is not None and state.dispute.flagged_events
    checklist = build_checklist(
        state.dispute.flagged_events, voyage_documents=["cp", "nor", "sof"]
    )
    assert checklist.items, "Rotterdam fixture must produce ≥1 evidence row"
    # The Rotterdam analyst should ask for a weather observation; we classify
    # those into a dedicated role.
    roles = {item.role for item in checklist.items}
    assert "weather_observation" in roles
    # CP clauses cited get an explicit cp_excerpt row.
    assert "cp_excerpt" in roles


def test_cp_excerpt_attached_iff_cp_uploaded() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    assert state.dispute is not None
    with_cp = build_checklist(
        state.dispute.flagged_events, voyage_documents=["cp", "nor", "sof"]
    )
    without_cp = build_checklist(
        state.dispute.flagged_events, voyage_documents=["nor", "sof"]
    )
    cp_with = [i for i in with_cp.items if i.role == "cp_excerpt"]
    cp_without = [i for i in without_cp.items if i.role == "cp_excerpt"]
    assert cp_with and all(i.attached for i in cp_with)
    assert cp_without and all(not i.attached for i in cp_without)


def test_weather_observation_attached_when_research_bundle_covers_event() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    assert state.dispute is not None
    # Pick the first flagged event id and fabricate a research bundle that
    # covers it. The checklist should mark the weather row attached.
    event_id = state.dispute.flagged_events[0].event_id
    bundle = EvidenceBundle(
        items=[
            ResearchEvidence(
                event_id=event_id,
                source="Rotterdam Port Authority",
                observed_value="0.2 mm/hr precipitation",
                supports="owner",
                citation="port-rotterdam",
                summary="Sub-threshold rainfall on the day of the stoppage.",
            )
        ]
    )
    checklist = build_checklist(
        state.dispute.flagged_events,
        voyage_documents=["cp", "nor", "sof"],
        evidence_bundle=bundle,
    )
    weather = [
        i for i in checklist.items if i.role == "weather_observation" and i.supports_event_id == event_id
    ]
    assert weather and all(i.attached for i in weather)


def test_unknown_evidence_lines_fall_into_other_not_dropped() -> None:
    # Synthesise a flagged event whose evidence_required line does not match
    # any of the known role cues; the checklist must surface it as 'other',
    # never silently drop it.
    fe = SimpleNamespace(
        event_id="e_synth",
        clauses_cited=[],
        evidence_required=["Some bespoke piece of evidence about XYZ"],
    )
    checklist = build_checklist([fe], voyage_documents=["cp", "nor", "sof"])
    assert any(i.role == "other" for i in checklist.items)


# ---------------------------------------------------------------------------
# time_bar_risk
# ---------------------------------------------------------------------------


def test_time_bar_risk_thresholds() -> None:
    assert time_bar_risk(60) == "Strong"
    assert time_bar_risk(46) == "Strong"
    assert time_bar_risk(45) == "Arguable"
    assert time_bar_risk(20) == "Arguable"
    assert time_bar_risk(15) == "Arguable"
    assert time_bar_risk(14) == "Weak"
    assert time_bar_risk(1) == "Weak"
    assert time_bar_risk(0) == "Weak"
    assert time_bar_risk(-3) == "Weak"
    assert time_bar_risk(None) == "Arguable"


# ---------------------------------------------------------------------------
# evidence_completeness derived from the checklist
# ---------------------------------------------------------------------------


def _checklist(*items: EvidenceItem) -> EvidenceChecklist:
    return EvidenceChecklist(items=list(items))


def test_evidence_completeness_strong_when_all_attached() -> None:
    cl = _checklist(
        EvidenceItem(role="cp_excerpt", label="CP 14", supports_event_id="e1", attached=True),
        EvidenceItem(role="nor", label="NOR copy", supports_event_id="e1", attached=True),
    )
    assert evidence_completeness_from_checklist("e1", cl) == "Strong"


def test_evidence_completeness_arguable_at_half_or_more() -> None:
    cl = _checklist(
        EvidenceItem(role="cp_excerpt", label="CP 14", supports_event_id="e1", attached=True),
        EvidenceItem(role="nor", label="NOR copy", supports_event_id="e1", attached=False),
    )
    assert evidence_completeness_from_checklist("e1", cl) == "Arguable"


def test_evidence_completeness_weak_below_half() -> None:
    cl = _checklist(
        EvidenceItem(role="cp_excerpt", label="CP 14", supports_event_id="e1", attached=False),
        EvidenceItem(role="nor", label="NOR copy", supports_event_id="e1", attached=False),
        EvidenceItem(role="sof", label="SoF row", supports_event_id="e1", attached=True),
    )
    assert evidence_completeness_from_checklist("e1", cl) == "Weak"


def test_evidence_completeness_weak_when_no_rows_for_event() -> None:
    cl = _checklist(
        EvidenceItem(role="cp_excerpt", label="CP 14", supports_event_id="other", attached=True),
    )
    assert evidence_completeness_from_checklist("e1", cl) == "Weak"


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------


def test_build_panels_keys_off_event_id_and_falls_back_to_arguable() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    assert state.dispute is not None
    checklist = build_checklist(
        state.dispute.flagged_events, voyage_documents=["cp", "nor", "sof"]
    )
    # Provide a model panel for the first event only; the rest should default
    # to ("Arguable", "Arguable").
    first_id = state.dispute.flagged_events[0].event_id
    panels = build_panels(
        flagged_events=state.dispute.flagged_events,
        model_panels={first_id: ("Strong", "Weak")},
        days_until_time_bar=60,
        checklist=checklist,
    )
    panel_by_event = {p.event_id: p.sub_scores for p in panels}
    assert panel_by_event[first_id].clause_clarity == "Strong"
    assert panel_by_event[first_id].counterparty_pushback_risk == "Weak"
    # Every panel inherits the deterministic time_bar_risk.
    for p in panels:
        assert p.sub_scores.time_bar_risk == "Strong"


def test_build_panels_time_bar_risk_overrides_anything_model_says() -> None:
    state = demo_voyage_fixture("v_test", "owner")
    assert state.dispute is not None
    checklist = build_checklist(
        state.dispute.flagged_events, voyage_documents=["cp", "nor", "sof"]
    )
    panels = build_panels(
        flagged_events=state.dispute.flagged_events,
        model_panels={},
        days_until_time_bar=3,  # urgent → Weak
        checklist=checklist,
    )
    assert all(p.sub_scores.time_bar_risk == "Weak" for p in panels)
