"""Agent 4 — Claims Drafter.

Takes the extraction, the calculated laytime, and the dispute analysis and
produces the ClaimPacket: a BIMCO-style claim letter, a dispute narrative, and
the summary fields. One Sonnet 4.6 structured-output call for the prose; every
number and date is then re-derived deterministically and overwritten so the
headline quantum and time-bar can never drift from the calculation.

"Streaming" (notes/03/11): the HTTP surface returns the full VoyageState on poll
(no SSE), so the "live letter" effect comes from the pipeline's staged store
updates, not token streaming. This call uses the same non-streaming structured
path as the rest of the fleet.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel

from ..schemas import (
    ClaimPacket,
    DisputeAnalysis,
    ExtractionResult,
    LaytimeResult,
    Perspective,
)
from ..prompts import load_prompt
from .llm import cached_system, extract_structured


class _DraftedClaim(BaseModel):
    """Prose-only projection of the ClaimPacket for the LLM call.

    The model writes only the narrative fields. Every number and date is
    re-derived deterministically in Python and never asked of the model — that
    way a model degeneration can't produce an out-of-range numeric field and
    fail the whole packet parse (numbers can still appear inside the prose as
    plain text, where a glitch is non-fatal).
    """

    executive_summary: str
    dispute_narrative_markdown: str
    claim_letter_markdown: str
    supporting_documents: list[str]

_BASE = Path(__file__).resolve().parent.parent
_PROMPT = (_BASE / "prompts" / "drafter.md").read_text()
_TEMPLATE = (_BASE / "letter_template.html").read_text()
# Shared cross-cutting rules prepended to the drafter system prompt.
_CROSS_CUTTING = load_prompt("cross_cutting")


def _eur(value: float) -> str:
    """Format as the canonical 'EUR' figure body: '84,375.00' (no prefix)."""
    return f"{value:,.2f}"


def _time_bar(extraction: ExtractionResult) -> tuple[str, int, bool]:
    """Deterministic time bar: (discharge completion + time_bar_days).

    Returns (time_bar_date_iso, days_until_time_bar, submitted_within_time_bar).
    """
    events = extraction.statement_of_facts.events
    completion = next(
        (e.timestamp for e in reversed(events) if e.category == "ops_end"),
        None,
    )
    if completion is None:
        completion = max((e.timestamp for e in events), default=None)
    completion_date = completion.date() if completion is not None else date.today()

    days = extraction.charter_party.time_bar_days or 90
    bar_date = completion_date + timedelta(days=days)
    today = date.today()
    return bar_date.isoformat(), (bar_date - today).days, today <= bar_date


def _system_text(extraction: ExtractionResult, perspective: Perspective) -> str:
    cp = extraction.charter_party
    clause_text = "\n".join(
        f"- Clause {c.clause_no}: {c.text}" for c in cp.clause_excerpts
    )
    return (
        f"{_CROSS_CUTTING}\n\n"
        f"{_PROMPT}\n\n"
        f"Perspective: {perspective}\n\n"
        f"LETTER TEMPLATE (follow exactly, fill the slots):\n{_TEMPLATE}\n\n"
        f"Charter-party clause excerpts (cite by number):\n{clause_text}"
    )


def _user_text(
    extraction: ExtractionResult,
    laytime: LaytimeResult,
    dispute: DisputeAnalysis,
    perspective: Perspective,
    bar_date: str,
    days_until: int,
    within_bar: bool,
) -> str:
    cp = extraction.charter_party
    sof = extraction.statement_of_facts
    flagged = [
        {
            "event_id": fe.event_id,
            "title": fe.title,
            "summary": fe.summary,
            "owner_argument": fe.owner_argument,
            "charterer_argument": fe.charterer_argument,
            "incremental_demurrage_eur": _eur(fe.incremental_demurrage_eur),
            "clauses_cited": fe.clauses_cited,
            "evidence_required": fe.evidence_required,
        }
        for fe in dispute.flagged_events
    ]
    payload = {
        "perspective": perspective,
        "charter_party": {
            "vessel": cp.vessel_name,
            "owner": cp.owner,
            "charterer": cp.charterer,
            "load_port": cp.load_port,
            "discharge_port": cp.discharge_port,
            "cp_date": cp.cp_date,
            "laytime_basis": cp.laytime_basis,
            "time_bar_days": cp.time_bar_days or 90,
        },
        "authoritative_figures_use_verbatim": {
            "laytime_allowed_hours": laytime.laytime_allowed_hours,
            "laytime_used_hours": laytime.laytime_used_hours,
            "time_on_demurrage_hours": laytime.time_on_demurrage_hours,
            "demurrage_rate_per_day_eur": _eur(cp.demurrage_rate_eur_per_day),
            "quantum_eur": _eur(laytime.demurrage_due_eur),
            "time_bar_date": bar_date,
            "days_until_time_bar": days_until,
            "submitted_within_time_bar": within_bar,
        },
        "statement_of_facts": {
            "port": sof.port,
            "events": [
                {"id": e.id, "timestamp": e.timestamp.isoformat(),
                 "description": e.description, "category": e.category}
                for e in sof.events
            ],
        },
        "dispute": {
            "overall_confidence": dispute.overall_confidence,
            "narrative_paragraphs": dispute.narrative_paragraphs,
            "flagged_events": flagged,
        },
    }
    return (
        f"Draft the claim packet from the {perspective}'s position using the "
        "BIMCO template. Use the authoritative figures verbatim:\n"
        + json.dumps(payload, indent=2)
    )


async def run(
    extraction: ExtractionResult,
    laytime: LaytimeResult,
    dispute: DisputeAnalysis,
    perspective: Perspective,
) -> ClaimPacket:
    """Produce the ClaimPacket. Prose from the model; all numbers/dates from Python."""
    bar_date, days_until, within_bar = _time_bar(extraction)

    drafted = await extract_structured(
        _DraftedClaim,
        system=cached_system(_system_text(extraction, perspective)),
        user_text=_user_text(
            extraction, laytime, dispute, perspective, bar_date, days_until, within_bar
        ),
        max_tokens=8192,
    )

    # Assemble the packet: prose from the model, money and dates from Python.
    return ClaimPacket(
        quantum_eur=laytime.demurrage_due_eur,
        executive_summary=drafted.executive_summary,
        dispute_narrative_markdown=drafted.dispute_narrative_markdown,
        claim_letter_markdown=drafted.claim_letter_markdown,
        supporting_documents=drafted.supporting_documents,
        time_bar_date=bar_date,
        submitted_within_time_bar=within_bar,
        days_until_time_bar=days_until,
    )
