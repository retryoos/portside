"""Claim strength sub-scores (notes/architecture_weeks_5_to_8.md §1.5).

Feature-local wire model that decomposes the single
``FlaggedEvent.owner_position_strength`` float into four named words so the
recipient gets a credible breakdown (not a number) of why a flag reads as it
does. Sits next to the analyst rather than in the frozen schema.

The four sub-scores
-------------------

- ``clause_clarity``: how unambiguously the CP clause supports the position.
- ``evidence_completeness``: do we actually have every document the argument
  needs (resolved against the EvidenceChecklist, not the model's view).
- ``counterparty_pushback_risk``: predicted likelihood the counterparty rejects.
- ``time_bar_risk``: derived deterministically from days_until_time_bar.

``time_bar_risk`` is never asked of the model. ``evidence_completeness`` is
re-derived deterministically post-call from the evidence checklist for the
same event. The other two come from an extended analyst prompt and stay
heuristic until we have a labelled dataset (see §1.5 calibration plan).
"""

from __future__ import annotations

from typing import Iterable, Literal, Optional

from pydantic import BaseModel

from .evidence_checklist import EvidenceChecklist

Strength = Literal["Strong", "Arguable", "Weak"]


class ClaimStrengthSubScores(BaseModel):
    """Per-event sub-score panel. Surfaced alongside the existing
    owner_position_strength float; we do not remove the float so callers that
    do not yet read sub-scores keep working."""

    clause_clarity: Strength
    evidence_completeness: Strength
    counterparty_pushback_risk: Strength
    time_bar_risk: Strength


class FlaggedEventStrength(BaseModel):
    """Sub-score panel + the event id it applies to. The analyst response
    embeds a list of these alongside the existing FlaggedEvent list, keyed by
    event_id so we never have to renumber the frozen FlaggedEvent rows."""

    event_id: str
    sub_scores: ClaimStrengthSubScores


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------


def time_bar_risk(days_until_time_bar: Optional[int]) -> Strength:
    """Maps the remaining time-bar days to a word.

    Thresholds chosen against the contractual 90-day default:
      - ``> 45``: Strong (plenty of time to assemble + file)
      - ``> 14``: Arguable (workable but tight)
      - otherwise: Weak (urgent; filing risk dominates the position)
    """
    if days_until_time_bar is None:
        return "Arguable"
    if days_until_time_bar > 45:
        return "Strong"
    if days_until_time_bar > 14:
        return "Arguable"
    return "Weak"


def evidence_completeness_from_checklist(
    event_id: str, checklist: EvidenceChecklist
) -> Strength:
    """Derive ``evidence_completeness`` from the EvidenceChecklist rows
    attached to ``event_id``.

    Rule: every checklist row that targets this event must have
    ``attached=True`` for Strong; at least half attached for Arguable; below
    half (or zero rows) for Weak. The model never owns this; it is a count.
    """
    relevant = [item for item in checklist.items if item.supports_event_id == event_id]
    if not relevant:
        return "Weak"
    attached = sum(1 for item in relevant if item.attached)
    ratio = attached / len(relevant)
    if ratio >= 0.999:
        return "Strong"
    if ratio >= 0.5:
        return "Arguable"
    return "Weak"


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------


def build_panel(
    *,
    event_id: str,
    model_emitted_clause_clarity: Strength,
    model_emitted_pushback_risk: Strength,
    days_until_time_bar: Optional[int],
    checklist: EvidenceChecklist,
) -> FlaggedEventStrength:
    """Compose the sub-score panel for a single flagged event.

    Two of the four sub-scores come from Python (``time_bar_risk`` and
    ``evidence_completeness``). The other two are passed in from the model.
    The model never sees the deterministic two; it cannot pull the panel
    toward an answer that contradicts the calendar or the documents.
    """
    return FlaggedEventStrength(
        event_id=event_id,
        sub_scores=ClaimStrengthSubScores(
            clause_clarity=model_emitted_clause_clarity,
            evidence_completeness=evidence_completeness_from_checklist(
                event_id, checklist
            ),
            counterparty_pushback_risk=model_emitted_pushback_risk,
            time_bar_risk=time_bar_risk(days_until_time_bar),
        ),
    )


def derive_model_panel_from_event(
    owner_position_strength: float,
) -> tuple[Strength, Strength]:
    """Deterministic v0.1 fallback for the two model-owned sub-scores.

    Maps ``owner_position_strength`` (already calibrated by the analyst) into
    ``(clause_clarity, counterparty_pushback_risk)``. The mapping is the
    obvious one: a strong owner position implies the clause reads clearly in
    the owner's favour AND that the charterer has limited room to push back.
    Replaced in v0.2 by an extended analyst prompt that emits the two words
    directly (see §1.5 calibration plan).
    """
    if owner_position_strength >= 0.7:
        return ("Strong", "Weak")
    if owner_position_strength >= 0.4:
        return ("Arguable", "Arguable")
    return ("Weak", "Strong")


def build_panels(
    *,
    flagged_events: Iterable,
    model_panels: dict[str, tuple[Strength, Strength]],
    days_until_time_bar: Optional[int],
    checklist: EvidenceChecklist,
) -> list[FlaggedEventStrength]:
    """Convenience: build one panel per event in one call.

    ``model_panels`` maps ``event_id -> (clause_clarity, pushback_risk)``,
    i.e. the two sub-scores the analyst is allowed to emit. Events without
    an entry get ``Arguable`` defaults on both, which surfaces in tests as
    a hint that the analyst prompt missed an event.
    """
    return [
        build_panel(
            event_id=getattr(fe, "event_id"),
            model_emitted_clause_clarity=model_panels.get(
                getattr(fe, "event_id"), ("Arguable", "Arguable")
            )[0],
            model_emitted_pushback_risk=model_panels.get(
                getattr(fe, "event_id"), ("Arguable", "Arguable")
            )[1],
            days_until_time_bar=days_until_time_bar,
            checklist=checklist,
        )
        for fe in flagged_events
    ]
