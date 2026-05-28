"""Agent 2 — Laytime Calculator.

Two parts:
  * 2a  classify_events  — LLM step (Sonnet 4.6), one call classifying every SoF
        event against the CP exception clauses. Added in the LLM build step.
  * 2b  calculate_laytime — deterministic Python arithmetic. The LLM never adds
        hours; this function does, so the numbers are reproducible and auditable.

This module owns BOTH halves per notes/15-next-phase.md (Agent 1's lane). The
deterministic half is the gate (tests/test_calculator.py).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from ..schemas import (
    EventClassification,
    ExtractionResult,
    LaytimeResult,
    LaytimeRow,
    Perspective,
    SoFEvent,
)
from ..prompts import load_prompt
from .llm import cached_system, extract_structured

# Categories that bound the laytime window.
_START_CATEGORY = "laytime_start"
_END_CATEGORY = "ops_end"


_CLASSIFIER_PROMPT = (
    Path(__file__).resolve().parent.parent / "prompts" / "classifier.md"
).read_text()
# Shared cross-cutting rules prepended to the classifier system prompt.
_CROSS_CUTTING = load_prompt("cross_cutting")


class _ClassificationBatch(BaseModel):
    """Wrapper so the structured-output call returns a list in one shot."""

    classifications: list[EventClassification]


async def classify_events(
    extraction: ExtractionResult,
    perspective: Perspective,
) -> list[EventClassification]:
    """Agent 2a — LLM classification of every SoF event against the CP clauses.

    One call for all events. The CP exception clauses go in the (cache-eligible)
    system text; the events go in the user message. No arithmetic here.
    """
    cp = extraction.charter_party
    clause_text = "\n".join(
        f"- Clause {c.clause_no}: {c.text}" for c in cp.clause_excerpts
    )
    system_text = (
        f"{_CROSS_CUTTING}\n\n"
        f"{_CLASSIFIER_PROMPT}\n\n"
        f"Perspective: {perspective}\n"
        f"Charter party form: {cp.form}; laytime basis: {cp.laytime_basis}.\n"
        f"Exception clauses in force: {', '.join(cp.exception_clauses)}.\n\n"
        f"Charter-party clause excerpts:\n{clause_text}"
    )
    events_payload = [
        {"id": e.id, "timestamp": e.timestamp.isoformat(), "description": e.description, "category": e.category}
        for e in extraction.statement_of_facts.events
    ]
    user_text = "Classify each of these Statement-of-Facts events:\n" + json.dumps(
        events_payload, indent=2
    )
    batch = await extract_structured(
        _ClassificationBatch,
        system=cached_system(system_text),
        user_text=user_text,
        max_tokens=4096,
    )
    return batch.classifications


def _duration_hours(a: SoFEvent, b: SoFEvent) -> float:
    return (b.timestamp - a.timestamp).total_seconds() / 3600.0


def _row(
    a: SoFEvent,
    b: SoFEvent,
    duration: float,
    counts: bool,
    status: str,
    reason: str,
    running_total: float,
    contestable: bool,
) -> LaytimeRow:
    return LaytimeRow.model_validate(
        {
            "from": a.timestamp,
            "to": b.timestamp,
            "duration_hours": round(duration, 4),
            "counts": counts,
            "status": status,
            "reason": reason,
            "running_total_hours": round(running_total, 4),
            "event_id_start": a.id,
            "event_id_end": b.id,
            "contestable": contestable,
        }
    )


def calculate_laytime(
    extraction: ExtractionResult,
    classifications: list[EventClassification],
) -> LaytimeResult:
    """Walk the SoF timeline and produce the per-event laytime table + quantum.

    Rules (standard voyage-charter, hard-coded for the MVP):
      * The window runs from the first ``laytime_start`` event to the last
        ``ops_end`` event.
      * Each interval [event_n, event_{n+1}) inherits event_n's classification.
        Excepted intervals (``counts_against_laytime`` False) do not accrue.
      * Counted hours accrue; once the running total exceeds the allowance the
        vessel is on demurrage. A counted interval straddling the allowance is
        split into a laytime row and a demurrage row at the crossover.
      * Demurrage due = hours on demurrage x (demurrage_rate_per_day / 24).
    """
    cp = extraction.charter_party
    allowed = cp.laytime_allowed_hours
    rate_per_hour = cp.demurrage_rate_eur_per_day / 24.0

    events = sorted(extraction.statement_of_facts.events, key=lambda e: e.timestamp)
    cls_by_id: dict[str, EventClassification] = {c.event_id: c for c in classifications}

    start_idx = next(
        (i for i, e in enumerate(events) if e.category == _START_CATEGORY), None
    )
    end_idx = next(
        (i for i in range(len(events) - 1, -1, -1) if events[i].category == _END_CATEGORY),
        None,
    )
    if start_idx is None or end_idx is None or end_idx <= start_idx:
        # Not enough structure to compute; return an empty, honest result.
        return LaytimeResult(
            laytime_allowed_hours=allowed,
            laytime_used_hours=0.0,
            time_on_demurrage_hours=0.0,
            time_excepted_hours=0.0,
            demurrage_rate_per_hour_eur=round(rate_per_hour, 4),
            demurrage_due_eur=0.0,
            despatch_due_eur=None,
            rows=[],
            classifications=classifications,
        )

    rows: list[LaytimeRow] = []
    running = 0.0  # counted hours
    excepted_total = 0.0

    for i in range(start_idx, end_idx):
        a, b = events[i], events[i + 1]
        dur = _duration_hours(a, b)
        cls = cls_by_id.get(a.id)
        counts = cls.counts_against_laytime if cls is not None else True
        contestable = cls.contestable if cls is not None else False
        reason = cls.clause_basis if cls is not None else "operational time"

        if not counts:
            excepted_total += dur
            rows.append(_row(a, b, dur, False, "excepted", reason, running, contestable))
            continue

        if running < allowed and running + dur > allowed:
            # Split at the allowance crossover.
            first = allowed - running
            running = allowed
            rows.append(_row(a, b, first, True, "laytime", reason, running, contestable))
            second = dur - first
            running += second
            rows.append(_row(a, b, second, True, "demurrage", reason, running, contestable))
        else:
            running += dur
            status = "demurrage" if running > allowed else "laytime"
            rows.append(_row(a, b, dur, True, status, reason, running, contestable))

    used = running
    on_demurrage = max(0.0, used - allowed)
    despatch = None
    if used < allowed and cp.despatch_rate_eur_per_day:
        despatch = round((allowed - used) * (cp.despatch_rate_eur_per_day / 24.0), 2)

    return LaytimeResult(
        laytime_allowed_hours=allowed,
        laytime_used_hours=round(used, 4),
        time_on_demurrage_hours=round(on_demurrage, 4),
        time_excepted_hours=round(excepted_total, 4),
        demurrage_rate_per_hour_eur=round(rate_per_hour, 4),
        demurrage_due_eur=round(on_demurrage * rate_per_hour, 2),
        despatch_due_eur=despatch,
        rows=rows,
        classifications=classifications,
    )
