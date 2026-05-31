"""Evidence checklist (notes/architecture_weeks_5_to_8.md §1.4).

Feature-local wire model + the deterministic builder that pairs each
``FlaggedEvent.evidence_required`` line with a concrete document role and an
``attached`` boolean. Living next to the drafter rather than in the frozen
``schemas.py``; the route layer surfaces ``EvidenceChecklist`` as a sibling
field on the response so the existing ``ClaimPacket`` schema stays untouched.

Why deterministic. ``attached`` is a fact about what is on the server, not
an opinion the model is allowed to form. We compute it after the drafter
runs by walking ``voyage.documents`` and the research-agent evidence bundle.
The model's only contribution is the ``label`` and ``note`` text on each row.
"""

from __future__ import annotations

import re
from typing import Iterable, Literal, Optional

from pydantic import BaseModel, Field

from .researcher import EvidenceBundle

EvidenceRole = Literal[
    "cp_excerpt",
    "nor",
    "sof",
    "bunker_note",
    "port_log",
    "weather_observation",
    "agent_correspondence",
    "other",
]


class EvidenceItem(BaseModel):
    """One row in the recipient-facing evidence checklist.

    ``attached`` is set deterministically post-call. The model never owns it.
    """

    role: EvidenceRole
    label: str = Field(..., min_length=2)
    supports_event_id: Optional[str] = None
    supports_clause: Optional[str] = None
    attached: bool
    source_voyage_doc_id: Optional[str] = None
    note: Optional[str] = None


class EvidenceChecklist(BaseModel):
    """Bag of ``EvidenceItem`` rows. Surfaced as a sibling to ``ClaimPacket``
    so the frozen schema is unaffected."""

    items: list[EvidenceItem]


# ---------------------------------------------------------------------------
# Heuristic role mapping
# ---------------------------------------------------------------------------

# Drives the role classification from the free-text "evidence_required" lines
# the analyst emits today. Conservative: any line that does not match a
# known cue falls into "other" rather than being silently dropped.
_ROLE_CUES: list[tuple[EvidenceRole, tuple[str, ...]]] = [
    ("weather_observation", ("weather", "precipitation", "rain", "wind", "observation")),
    ("port_log", ("port log", "portlog", "berth log")),
    ("agent_correspondence", ("agent", "email", "correspondence", "telex")),
    ("bunker_note", ("bunker", "bdn", "bunker delivery")),
    ("nor", ("notice of readiness", "nor")),
    ("sof", ("statement of facts", "sof", "timesheet")),
    ("cp_excerpt", ("charter party", "cp clause", "clause", "charter-party")),
]


def _classify_role(text: str) -> EvidenceRole:
    needle = text.lower()
    for role, cues in _ROLE_CUES:
        if any(cue in needle for cue in cues):
            return role
    return "other"


_CLAUSE_RE = re.compile(r"clause\s+([0-9]+[A-Za-z]?)", re.IGNORECASE)


def _extract_clause(text: str) -> Optional[str]:
    m = _CLAUSE_RE.search(text)
    return f"Clause {m.group(1)}" if m else None


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_checklist(
    flagged_events: Iterable,
    *,
    voyage_documents: Iterable[str],
    evidence_bundle: Optional[EvidenceBundle] = None,
) -> EvidenceChecklist:
    """Compose the recipient-facing checklist from the dispute analysis +
    the documents actually on the server.

    ``flagged_events`` is the ``DisputeAnalysis.flagged_events`` list (passed
    duck-typed so this module does not pull in the frozen schema). Each event
    contributes one row per ``evidence_required`` entry, plus one row per
    clause cited (so the recipient sees both the textual evidence and the
    underlying clause). ``voyage_documents`` is the role tags of the docs the
    user already uploaded (``"cp"``, ``"nor"``, ``"sof"``); we use it for the
    ``attached`` boolean on the corresponding rows.
    """
    uploaded_roles = {d.lower() for d in voyage_documents}
    evidence_event_ids = (
        {item.event_id for item in evidence_bundle.items}
        if evidence_bundle is not None
        else set()
    )

    items: list[EvidenceItem] = []
    seen: set[tuple[EvidenceRole, str, Optional[str]]] = set()

    for fe in flagged_events:
        event_id: Optional[str] = getattr(fe, "event_id", None)
        for required in getattr(fe, "evidence_required", []) or []:
            role = _classify_role(required)
            label = required.strip()
            clause = _extract_clause(label) or _first(
                getattr(fe, "clauses_cited", []) or []
            )
            key = (role, label.lower(), event_id)
            if key in seen:
                continue
            seen.add(key)

            attached = _is_attached(
                role,
                event_id=event_id,
                uploaded_roles=uploaded_roles,
                evidence_event_ids=evidence_event_ids,
            )
            items.append(
                EvidenceItem(
                    role=role,
                    label=label,
                    supports_event_id=event_id,
                    supports_clause=clause,
                    attached=attached,
                    note=None,
                )
            )

        # Add an explicit CP-clause excerpt row per clause cited, since the
        # recipient often wants the contractual hook listed even when the
        # analyst phrased the evidence_required line in terms of facts only.
        for clause in getattr(fe, "clauses_cited", []) or []:
            clause_label = f"Charter party {clause}"
            key = ("cp_excerpt", clause_label.lower(), event_id)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                EvidenceItem(
                    role="cp_excerpt",
                    label=clause_label,
                    supports_event_id=event_id,
                    supports_clause=clause,
                    attached="cp" in uploaded_roles,
                )
            )

    return EvidenceChecklist(items=items)


def _first(iterable: Iterable[str]) -> Optional[str]:
    for item in iterable:
        return item
    return None


def _is_attached(
    role: EvidenceRole,
    *,
    event_id: Optional[str],
    uploaded_roles: set[str],
    evidence_event_ids: set[str],
) -> bool:
    if role == "cp_excerpt":
        return "cp" in uploaded_roles
    if role == "nor":
        return "nor" in uploaded_roles
    if role == "sof":
        return "sof" in uploaded_roles
    if role == "weather_observation":
        return event_id is not None and event_id in evidence_event_ids
    # Conservative default: anything outside our role taxonomy is not yet
    # attached until a future ingest path (email-in, manual upload) wires it.
    return False
