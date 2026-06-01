"""A6 — Defence (charterer rebuttal) on top of a stored owner voyage.

The numbers are owned by deterministic Python — the model never picks a euro.
``recompute_after_concessions`` is the gate: winning the contested 4h weather
stoppage on the Rotterdam demo drops the quantum from EUR 84,375.00 to
EUR 76,875.00, locked by ``tests/test_defense.py``.

The rebuttal letter is drafted by the model when an Anthropic API key is
available; otherwise we fall back to a deterministic template so ``/rebut``
always returns a valid packet (offline-safe). Schemas stay FROZEN: the
``RebuttalPacket`` / ``RebuttalPoint`` models live here, not in ``schemas.py``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel

from .agents.llm import cached_system, extract_structured
from .schemas import (
    DisputeAnalysis,
    ExtractionResult,
    LaytimeResult,
    VoyageState,
)

logger = logging.getLogger("laytimely_api")

_PROMPT = (Path(__file__).resolve().parent / "prompts" / "rebuttal.md").read_text()


# --- feature-local wire models --------------------------------------------


class RebuttalPoint(BaseModel):
    event_id: str
    owner_claim: str
    charterer_response: str
    clause_cited: str
    swing_eur: float  # the amount that drops if the charterer wins this point


class RebuttalPacket(BaseModel):
    original_quantum_eur: float
    conceded_eur: float  # what the charterer accepts (= reduced_quantum_eur)
    contested_eur: float  # the amount the charterer disputes
    reduced_quantum_eur: float
    rebuttal_letter_markdown: str
    points: list[RebuttalPoint]


class _RebuttalLetterDraft(BaseModel):
    rebuttal_letter_markdown: str


# --- deterministic core (the gate) ----------------------------------------


def won_event_ids(laytime: LaytimeResult) -> list[str]:
    """Events the charterer contests: every contestable row sitting in demurrage.

    For the demo this is exactly the 4h weather stoppage at e6. Sorted so the
    output is stable across runs.
    """
    return sorted(
        {
            r.event_id_start
            for r in laytime.rows
            if r.contestable and r.status == "demurrage"
        }
    )


def recompute_after_concessions(
    laytime: LaytimeResult, won_ids: list[str]
) -> tuple[float, float, float]:
    """Return (reduced_quantum_eur, conceded_eur, contested_eur).

    Only demurrage-status contested hours reduce the quantum (hours that fell
    inside the laytime allowance never produced demurrage in the first place).
    ``conceded_eur`` equals ``reduced_quantum_eur``: it is the amount the
    charterer accepts is properly due.
    """
    rate = laytime.demurrage_rate_per_hour_eur
    won = set(won_ids)
    won_hours = sum(
        r.duration_hours
        for r in laytime.rows
        if r.contestable
        and r.status == "demurrage"
        and r.event_id_start in won
    )
    contested = round(won_hours * rate, 2)
    original = laytime.demurrage_due_eur
    reduced = round(original - contested, 2)
    return reduced, reduced, contested


def build_rebuttal_points(
    laytime: LaytimeResult, dispute: DisputeAnalysis
) -> list[RebuttalPoint]:
    rate = laytime.demurrage_rate_per_hour_eur
    points: list[RebuttalPoint] = []
    for fe in dispute.flagged_events:
        hours = sum(
            r.duration_hours
            for r in laytime.rows
            if r.contestable
            and r.status == "demurrage"
            and r.event_id_start == fe.event_id
        )
        points.append(
            RebuttalPoint(
                event_id=fe.event_id,
                owner_claim=fe.owner_argument,
                charterer_response=fe.charterer_argument,
                clause_cited=fe.clauses_cited[0] if fe.clauses_cited else "",
                swing_eur=round(hours * rate, 2),
            )
        )
    return points


# --- letter (LLM with deterministic fallback) -----------------------------


def _template_letter(
    extraction: ExtractionResult,
    original: float,
    reduced: float,
    contested: float,
    points: list[RebuttalPoint],
) -> str:
    cp = extraction.charter_party
    lines: list[str] = [
        f"**{cp.charterer}**",
        "",
        f"Re: Demurrage claim, {cp.vessel_name}, {cp.load_port} / {cp.discharge_port}",
        "",
        "We acknowledge the owners' demurrage claim. The charterer disputes the "
        "claim in part for the reasons set out below.",
        "",
        "**Summary**",
        f"- Owners' claimed demurrage: EUR {original:,.2f}",
        f"- Amount contested by the charterer: EUR {contested:,.2f}",
        f"- Amount the charterer accepts as properly due: EUR {reduced:,.2f}",
        "",
        "**Points**",
    ]
    for p in points:
        lines.append(
            f"- **{p.event_id}** ({p.clause_cited}, swing EUR {p.swing_eur:,.2f}). "
            f"Owners contend: {p.owner_claim} "
            f"Charterers respond: {p.charterer_response}"
        )
    lines.extend(
        [
            "",
            "Accordingly the charterer's position is that demurrage of "
            f"EUR {reduced:,.2f} is properly due. All rights reserved.",
        ]
    )
    return "\n".join(lines)


async def draft_rebuttal_letter(
    extraction: ExtractionResult,
    original: float,
    reduced: float,
    contested: float,
    points: list[RebuttalPoint],
) -> str:
    """LLM-drafted rebuttal letter, with a deterministic fallback so ``/rebut``
    never hard-fails offline (no API key) or on transient model errors."""
    cp = extraction.charter_party
    payload = {
        "charterer": cp.charterer,
        "vessel": cp.vessel_name,
        "load_port": cp.load_port,
        "discharge_port": cp.discharge_port,
        "cp_date": cp.cp_date,
        "points": [p.model_dump() for p in points],
    }
    system_text = (
        f"{_PROMPT}\n\n"
        "Locked figures you MUST quote verbatim (do not recompute):\n"
        f"- Owners' claim: EUR {original:,.2f}\n"
        f"- Contested by the charterer: EUR {contested:,.2f}\n"
        f"- Reduced quantum (charterer's position): EUR {reduced:,.2f}\n"
    )
    user_text = "Draft the charterer's rebuttal letter from this brief:\n" + json.dumps(
        payload, indent=2
    )
    try:
        result = await extract_structured(
            _RebuttalLetterDraft,
            system=cached_system(system_text),
            user_text=user_text,
            max_tokens=2048,
        )
        return result.rebuttal_letter_markdown
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning("rebuttal letter LLM draft failed; using template: %s", exc)
        return _template_letter(extraction, original, reduced, contested, points)


# --- top-level orchestration ----------------------------------------------


async def build_rebuttal_packet(voyage: VoyageState) -> RebuttalPacket:
    """Assemble the RebuttalPacket from a stored owner voyage."""
    if voyage.extraction is None or voyage.laytime is None or voyage.dispute is None:
        raise ValueError("voyage is not ready for rebuttal")
    won = won_event_ids(voyage.laytime)
    reduced, conceded, contested = recompute_after_concessions(voyage.laytime, won)
    points = build_rebuttal_points(voyage.laytime, voyage.dispute)
    letter = await draft_rebuttal_letter(
        voyage.extraction, voyage.laytime.demurrage_due_eur, reduced, contested, points
    )
    return RebuttalPacket(
        original_quantum_eur=voyage.laytime.demurrage_due_eur,
        conceded_eur=conceded,
        contested_eur=contested,
        reduced_quantum_eur=reduced,
        rebuttal_letter_markdown=letter,
        points=points,
    )
