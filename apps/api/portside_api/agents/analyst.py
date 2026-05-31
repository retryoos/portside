"""Agent 3 — Dispute Analyst.

Reads the extraction + the calculated laytime result and writes the legal
argument for each contested window, with CP-clause and SoF-event citations and a
calibrated confidence. One Sonnet 4.6 call via the structured-output path. See
notes/03-agents.md "Agent 3" and notes/11-prompts.md "Agent 3".

Money is never trusted from the model: ``incremental_demurrage_eur`` is
re-derived deterministically from the contested laytime rows after the call.

Citations (W0, notes/architecture_weeks_5_to_8.md §1.6)
-------------------------------------------------------

After the dispute brief is produced, ``run_with_citations`` adds a list of
verified ``CitedAuthority`` rows per flagged event. The model never invents
citations:

1. We BM25-search the curated corpus (deterministic Python) with the event's
   own facts (title + summary + clauses cited).
2. We pass the top hits to a focused, second Sonnet call whose ONLY job is
   to pick 0..3 of them and write a one-line proposition each.
3. The picks are mapped back through the candidate list, so the model
   physically cannot reference a case_id that did not come from a real corpus
   row.
4. ``legal.verify.validate_authorities`` runs anyway as belt-and-braces
   against future tool surfaces (IMO, EUR-Lex) that might join the loop.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from ..legal import corpus as legal_corpus
from ..legal import verify as legal_verify
from ..legal.models import CitedAuthority
from ..schemas import (
    DisputeAnalysis,
    ExtractionResult,
    FlaggedEvent,
    LaytimeResult,
    Perspective,
)
from ..prompts import load_prompt
from .llm import cached_system, extract_structured

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "analyst.md").read_text()
# Shared cross-cutting rules prepended to the analyst system prompt.
_CROSS_CUTTING = load_prompt("cross_cutting")

# How many top corpus hits we pass to the picker per event.
_CITATION_TOP_K = 5
# Cap how many citations the model is allowed to choose per event. Three keeps
# the letter readable; the picker prompt enforces this too but a Python clamp
# is the truth.
_CITATIONS_PER_EVENT_CAP = 3


# ---------------------------------------------------------------------------
# Feature-local wire models
# ---------------------------------------------------------------------------


class FlaggedEventCitations(BaseModel):
    """Per-flagged-event citation bundle.

    Sibling to the existing ``DisputeAnalysis.flagged_events`` list keyed by
    ``event_id`` so the frozen ``FlaggedEvent`` schema is untouched. The route
    layer (next PR) surfaces these alongside the dispute response."""

    event_id: str
    cited_authorities: list[CitedAuthority]


class EnrichedDisputeAnalysis(BaseModel):
    """``DisputeAnalysis`` plus the verified citations per flagged event."""

    analysis: DisputeAnalysis
    citations: list[FlaggedEventCitations]


# Picker output: the model returns case_ids (must come from the candidate
# list we sent) + a proposition. We map case_ids back to ``CaseHit`` rows and
# build ``CitedAuthority`` ourselves.
class _CitationPick(BaseModel):
    case_id: str
    proposition: str


class _CitationPicks(BaseModel):
    picks: list[_CitationPick]


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
    """Produce the DisputeAnalysis for the contested windows.

    Unchanged contract; the citations-enriched path is ``run_with_citations``.
    """
    analysis = await extract_structured(
        DisputeAnalysis,
        system=cached_system(_system_text(extraction, perspective)),
        user_text=_user_text(laytime, perspective),
        max_tokens=4096,
    )
    return _recompute_incremental(analysis, laytime)


async def run_with_citations(
    extraction: ExtractionResult,
    laytime: LaytimeResult,
    perspective: Perspective,
) -> EnrichedDisputeAnalysis:
    """``run`` + a citation pass over the curated corpus.

    Implementation:

    1. Run the existing dispute analysis.
    2. For each ``FlaggedEvent``, BM25-search the corpus with the event's
       facts (deterministic Python).
    3. Ask a small structured-output call to pick 0..3 candidates and write a
       one-line proposition each.
    4. Map picks back through the candidate list (the model cannot reference a
       ``case_id`` that did not come from real corpus row).
    5. Run ``verify.validate_authorities`` over the resulting authorities for
       belt-and-braces (matters when we later add IMO + EUR-Lex to the loop).
    """
    analysis = await run(extraction, laytime, perspective)
    citations: list[FlaggedEventCitations] = []
    for event in analysis.flagged_events:
        cited = await _citations_for_event(event)
        if cited:
            citations.append(
                FlaggedEventCitations(event_id=event.event_id, cited_authorities=cited)
            )
    return EnrichedDisputeAnalysis(analysis=analysis, citations=citations)


# ---------------------------------------------------------------------------
# Per-event citation gathering
# ---------------------------------------------------------------------------


def _citation_query(event: FlaggedEvent) -> str:
    """Compose a BM25 query from the event facts.

    Order matters: the title and summary carry the topic-bearing nouns; the
    cited clauses widen the lexical net to the contractual hooks; the
    evidence_required strings (when present) often name the kind of authority
    that helps."""
    parts: list[str] = [event.title, event.summary]
    for clause in event.clauses_cited or []:
        parts.append(clause)
    for evidence in event.evidence_required or []:
        parts.append(evidence)
    return " ".join(p for p in parts if p)


def _build_candidate_block(candidates) -> str:
    rows: list[str] = []
    for hit in candidates:
        rows.append(
            f"- case_id: {hit.case_id}\n"
            f"  citation: {hit.citation}\n"
            f"  headnote: {hit.headnote}"
        )
    return "\n".join(rows)


def _picker_user_text(event: FlaggedEvent, candidates_block: str) -> str:
    return (
        "You are picking maritime case authorities for a dispute event.\n\n"
        f"Event: {event.title}\n"
        f"Summary: {event.summary}\n"
        f"Owner's argument: {event.owner_argument}\n"
        f"Charterer's argument: {event.charterer_argument}\n\n"
        f"Candidate authorities (these are real; pick ONLY from this list):\n"
        f"{candidates_block}\n\n"
        f"Pick 0 to {_CITATIONS_PER_EVENT_CAP} authorities that genuinely "
        "support the position. For each, write ONE sentence saying how it "
        "applies to this dispute. The proposition must reference the "
        "principle, not paraphrase the headnote. Do not invent case_ids; "
        "use only those listed above. If no candidate is on point, return an "
        "empty picks list."
    )


_PICKER_SYSTEM = (
    "You select maritime case authorities for a dispute event. The candidate "
    "list is the only source; you cannot cite anything outside it. Quality "
    "over quantity: zero picks is fine if nothing is on point."
)


async def _pick_citations(
    event: FlaggedEvent, candidates
) -> _CitationPicks:
    """Run the picker call. Returns empty picks on any failure so a bad call
    never blocks the dispute from being saved."""
    if not candidates:
        return _CitationPicks(picks=[])
    block = _build_candidate_block(candidates)
    try:
        return await extract_structured(
            _CitationPicks,
            system=cached_system(_PICKER_SYSTEM),
            user_text=_picker_user_text(event, block),
            max_tokens=1024,
        )
    except Exception:  # noqa: BLE001 - boundary handler for the picker call
        return _CitationPicks(picks=[])


async def _citations_for_event(event: FlaggedEvent) -> list[CitedAuthority]:
    """End-to-end: query the corpus, ask the model to pick, validate, return."""
    query = _citation_query(event)
    candidates = legal_corpus.search(query, k=_CITATION_TOP_K)
    if not candidates:
        return []
    by_case_id = {hit.case_id: hit for hit in candidates}

    picks = await _pick_citations(event, candidates)

    chosen: list[CitedAuthority] = []
    seen: set[str] = set()
    for pick in picks.picks:
        # Hallucinated case_id: the candidate list is authoritative.
        hit = by_case_id.get(pick.case_id)
        if hit is None:
            continue
        if pick.case_id in seen:
            continue
        if not pick.proposition.strip():
            continue
        seen.add(pick.case_id)
        chosen.append(
            CitedAuthority(
                citation=hit.citation,
                verified_via_tool=True,
                tool_used="corpus",
                proposition=pick.proposition.strip(),
                url=hit.url,
            )
        )
        if len(chosen) >= _CITATIONS_PER_EVENT_CAP:
            break

    # Belt and braces: even though the candidates are real corpus rows, run
    # the standard verify gate over the citations + the headnote transcript.
    # This matters when we later add IMO + EUR-Lex tools to the same path.
    transcript = [f"{hit.citation} :: {hit.headnote}" for hit in candidates]
    return legal_verify.validate_authorities(chosen, transcript)
