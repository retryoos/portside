"""Agent 3 — Dispute Analyst.

Reads the extraction + the calculated laytime result and writes the legal
argument for each contested window, with CP-clause and SoF-event citations and a
calibrated confidence. One Sonnet 4.6 call via the structured-output path. See
notes/03-agents.md "Agent 3" and notes/11-prompts.md "Agent 3".

Money is never trusted from the model: ``incremental_demurrage_eur`` is
re-derived deterministically from the contested laytime rows after the call.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..schemas import (
    DisputeAnalysis,
    ExtractionResult,
    LaytimeResult,
    Perspective,
)
from ..prompts import load_prompt
from .llm import cached_system, extract_structured

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "analyst.md").read_text()
# Shared cross-cutting rules prepended to the analyst system prompt.
_CROSS_CUTTING = load_prompt("cross_cutting")


def _system_text(extraction: ExtractionResult, perspective: Perspective) -> str:
    """Prompt + perspective + verbatim CP clause excerpts (cache-eligible)."""
    cp = extraction.charter_party
    clause_text = "\n".join(
        f"- Clause {c.clause_no}: {c.text}" for c in cp.clause_excerpts
    )
    return (
        f"{_CROSS_CUTTING}\n\n"
        f"{_PROMPT}\n\n"
        f"Perspective: {perspective}\n"
        f"Charter party: {cp.vessel_name}, {cp.load_port} / {cp.discharge_port}, "
        f"form {cp.form}, CP dated {cp.cp_date}; laytime basis {cp.laytime_basis}.\n\n"
        f"Charter-party clause excerpts (cite these by number):\n{clause_text}"
    )


def _user_text(laytime: LaytimeResult, perspective: Perspective) -> str:
    """The calculated result, foregrounding the contested rows + classifications."""
    contested_rows = [
        {
            "event_id_start": r.event_id_start,
            "event_id_end": r.event_id_end,
            "from": r.from_ts.isoformat(),
            "to": r.to_ts.isoformat(),
            "duration_hours": r.duration_hours,
            "status": r.status,
            "reason": r.reason,
        }
        for r in laytime.rows
        if r.contestable
    ]
    classifications = [
        {
            "event_id": c.event_id,
            "counts_against_laytime": c.counts_against_laytime,
            "applicable_exception": c.applicable_exception,
            "clause_basis": c.clause_basis,
            "reasoning": c.reasoning,
            "contestable": c.contestable,
        }
        for c in laytime.classifications
    ]
    payload = {
        "perspective": perspective,
        "headline": {
            "laytime_allowed_hours": laytime.laytime_allowed_hours,
            "laytime_used_hours": laytime.laytime_used_hours,
            "time_on_demurrage_hours": laytime.time_on_demurrage_hours,
            "demurrage_rate_per_hour_eur": laytime.demurrage_rate_per_hour_eur,
            "demurrage_due_eur": laytime.demurrage_due_eur,
        },
        "contested_rows": contested_rows,
        "classifications": classifications,
    }
    return (
        "Analyse the contested time windows and produce the dispute brief from "
        f"the {perspective}'s position:\n" + json.dumps(payload, indent=2)
    )


def _recompute_incremental(
    analysis: DisputeAnalysis, laytime: LaytimeResult
) -> DisputeAnalysis:
    """Override each flagged event's incremental demurrage with the deterministic
    figure (contested-window hours x demurrage rate per hour). The LLM never owns
    a dollar figure."""
    rate = laytime.demurrage_rate_per_hour_eur
    for fe in analysis.flagged_events:
        hours = sum(
            r.duration_hours
            for r in laytime.rows
            if r.contestable and r.event_id_start == fe.event_id
        )
        if hours > 0:
            fe.incremental_demurrage_eur = round(hours * rate, 2)
    return analysis


async def run(
    extraction: ExtractionResult,
    laytime: LaytimeResult,
    perspective: Perspective,
) -> DisputeAnalysis:
    """Produce the DisputeAnalysis for the contested windows."""
    analysis = await extract_structured(
        DisputeAnalysis,
        system=cached_system(_system_text(extraction, perspective)),
        user_text=_user_text(laytime, perspective),
        max_tokens=4096,
    )
    return _recompute_incremental(analysis, laytime)
