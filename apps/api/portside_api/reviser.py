"""Agent 5 — inline revision micro-agent + server-side safety validation.

Backs the `/revise` surface (notes/13-inline-revision.md). A senior claims
executive selects text and asks the agent to refine it; the agent rewrites only
the flagged segments. Because a claim letter where the AI silently changed a
dollar amount, a clause number, or an event ID would be a catastrophic legal
failure, every rewrite is validated server-side AFTER the model responds:
monetary values, CP clause citations, and SoF event IDs must all be preserved,
or the revision is rejected (HTTP 422).

Request/response models live here (not in the FROZEN schemas.py) so this stretch
adds no risk to the core contract. The safety validator is pure stdlib and is
unit-tested without an API key (tests/test_reviser.py).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel

from .agents.llm import cached_system, extract_structured
from .schemas import VoyageState

SegmentSurface = Literal["letter", "narrative"]
ReviseMode = Literal["agent", "manual"]

_PROMPT = (Path(__file__).resolve().parent / "prompts" / "reviser.md").read_text()


# --------------------------------------------------------------------------- #
# Wire models (local to the stretch — schemas.py stays frozen)
# --------------------------------------------------------------------------- #


class ReviseSegment(BaseModel):
    id: str
    text: str


class ReviseRequest(BaseModel):
    surface: SegmentSurface
    segment_ids: list[str]
    instruction: str
    mode: ReviseMode = "agent"
    manual_text: Optional[str] = None
    segments: list[ReviseSegment]


class SafetyReport(BaseModel):
    quantum_unchanged: bool
    clauses_preserved: list[str]
    events_preserved: list[str]
    warnings: list[str]


class RevisedSegment(BaseModel):
    id: str
    surface: SegmentSurface
    text: str


class ReviseResponse(BaseModel):
    segments: list[RevisedSegment]
    safety: SafetyReport


class _SegmentRevision(BaseModel):
    """One agent rewrite (structured-output element)."""

    segment_id: str
    new_text: str
    rejection_reason: Optional[str] = None


class _SegmentRevisions(BaseModel):
    revisions: list[_SegmentRevision]


# --------------------------------------------------------------------------- #
# Safety validation (pure stdlib — the non-negotiable check)
# --------------------------------------------------------------------------- #

_EUR_RE = re.compile(r"EUR\s*([0-9][0-9,]*(?:\.[0-9]+)?)", re.IGNORECASE)
_CLAUSE_RE = re.compile(r"clause\s+([0-9]+[A-Za-z]?)", re.IGNORECASE)
_SECTION_RE = re.compile(r"§\s*([0-9]+[A-Za-z]?)")
_EVENT_RE = re.compile(r"\b(e[0-9]+)\b", re.IGNORECASE)


def _eur_values(text: str) -> set[float]:
    return {round(float(m.replace(",", "")), 2) for m in _EUR_RE.findall(text)}


def _clauses(text: str) -> set[str]:
    return {c.lower() for c in _CLAUSE_RE.findall(text) + _SECTION_RE.findall(text)}


def _events(text: str) -> set[str]:
    return {e.lower() for e in _EVENT_RE.findall(text)}


def validate_revision(old_text: str, new_text: str) -> tuple[bool, SafetyReport]:
    """Return (ok, report). A revision is rejected if any monetary value changed
    or any CP clause / SoF event reference was dropped or renumbered."""
    old_eur, new_eur = _eur_values(old_text), _eur_values(new_text)
    old_clauses, new_clauses = _clauses(old_text), _clauses(new_text)
    old_events, new_events = _events(old_text), _events(new_text)

    quantum_unchanged = old_eur == new_eur
    missing_clauses = old_clauses - new_clauses
    missing_events = old_events - new_events

    warnings: list[str] = []
    if not quantum_unchanged:
        warnings.append(
            f"monetary value changed: {sorted(old_eur)} -> {sorted(new_eur)}"
        )
    if missing_clauses:
        warnings.append(f"CP clause citation(s) dropped: {sorted(missing_clauses)}")
    if missing_events:
        warnings.append(f"SoF event ID(s) dropped: {sorted(missing_events)}")

    ok = quantum_unchanged and not missing_clauses and not missing_events
    report = SafetyReport(
        quantum_unchanged=quantum_unchanged,
        clauses_preserved=sorted(old_clauses & new_clauses),
        events_preserved=sorted(old_events & new_events),
        warnings=warnings,
    )
    return ok, report


# --------------------------------------------------------------------------- #
# The micro-agent + orchestration
# --------------------------------------------------------------------------- #


def _locked_summary(voyage: VoyageState) -> str:
    packet = voyage.packet
    if packet is None:
        return "Locked values: (none available yet)."
    return (
        "Locked values you must not alter — quantum "
        f"EUR {packet.quantum_eur:,.2f}, time-bar date {packet.time_bar_date}, "
        "and the supporting-documents list."
    )


def _surface_text(request: ReviseRequest) -> str:
    targets = set(request.segment_ids)
    parts = []
    for seg in request.segments:
        flag = ' revising="true"' if seg.id in targets else ""
        parts.append(f'<segment id="{seg.id}"{flag}>{seg.text}</segment>')
    return "\n".join(parts)


async def _run_agent(
    request: ReviseRequest, voyage: VoyageState
) -> list[_SegmentRevision]:
    system_text = f"{_PROMPT}\n\n{_locked_summary(voyage)}"
    user_text = (
        f"Instruction: {request.instruction}\n\n"
        f"Revise the segment(s) flagged revising=\"true\" "
        f"({', '.join(request.segment_ids)}). Full {request.surface}:\n"
        f"{_surface_text(request)}"
    )
    result = await extract_structured(
        _SegmentRevisions,
        system=cached_system(system_text),
        user_text=user_text,
        max_tokens=2048,
    )
    return result.revisions


def _merge(reports: list[SafetyReport]) -> SafetyReport:
    if not reports:
        return SafetyReport(
            quantum_unchanged=True, clauses_preserved=[], events_preserved=[], warnings=[]
        )
    clauses: set[str] = set()
    events: set[str] = set()
    warnings: list[str] = []
    quantum_unchanged = True
    for r in reports:
        quantum_unchanged = quantum_unchanged and r.quantum_unchanged
        clauses.update(r.clauses_preserved)
        events.update(r.events_preserved)
        warnings.extend(r.warnings)
    return SafetyReport(
        quantum_unchanged=quantum_unchanged,
        clauses_preserved=sorted(clauses),
        events_preserved=sorted(events),
        warnings=warnings,
    )


async def revise(
    request: ReviseRequest, voyage: VoyageState
) -> tuple[bool, ReviseResponse]:
    """Apply the revision. Returns (blocked, response). `blocked` is True when a
    rewrite failed safety validation (caller should answer HTTP 422)."""
    originals = {s.id: s.text for s in request.segments}

    # Manual edit: the human typed the new text; still validate it.
    if request.mode == "manual":
        target = request.segment_ids[0] if request.segment_ids else ""
        old_text = originals.get(target, "")
        new_text = request.manual_text or ""
        ok, report = validate_revision(old_text, new_text)
        text = new_text if ok else old_text
        response = ReviseResponse(
            segments=[RevisedSegment(id=target, surface=request.surface, text=text)],
            safety=report,
        )
        return (not ok, response)

    revisions = await _run_agent(request, voyage)

    revised: list[RevisedSegment] = []
    reports: list[SafetyReport] = []
    blocked = False
    extra_warnings: list[str] = []
    for rev in revisions:
        old_text = originals.get(rev.segment_id, "")
        if rev.rejection_reason:
            # The agent declined (constraint conflict) — keep the original, no block.
            revised.append(
                RevisedSegment(id=rev.segment_id, surface=request.surface, text=old_text)
            )
            extra_warnings.append(f"{rev.segment_id}: agent declined — {rev.rejection_reason}")
            continue
        ok, report = validate_revision(old_text, rev.new_text)
        reports.append(report)
        if ok:
            revised.append(
                RevisedSegment(id=rev.segment_id, surface=request.surface, text=rev.new_text)
            )
        else:
            blocked = True
            revised.append(
                RevisedSegment(id=rev.segment_id, surface=request.surface, text=old_text)
            )

    safety = _merge(reports)
    safety.warnings.extend(extra_warnings)
    return blocked, ReviseResponse(segments=revised, safety=safety)
