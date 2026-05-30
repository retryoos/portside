"""A7 — Evidence gathering ("research agents").

Fills the previously-unused ``FlaggedEvent.evidence_required`` hook with
externally-sourced observations. For each flagged event whose underlying SoF
event is a weather stoppage, the researcher calls ``tools.get_weather`` (the
fixture path keeps this offline) and emits an ``EvidenceItem`` whose
``supports`` value follows CP clause 14's 0.5 mm/hr threshold (above the
threshold supports the charterer's exception; below it supports the owner's
position). Deterministic by design: every figure can be re-derived.

Schemas stay FROZEN — these wire models live here, not in ``schemas.py``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .agents.tools import WeatherObservation, get_weather
from .schemas import DisputeAnalysis, ExtractionResult, SoFEvent

Supports = Literal["owner", "charterer", "neutral"]
_PRECIP_THRESHOLD_MM_PER_HR = 0.5  # CP clause 14


class EvidenceItem(BaseModel):
    event_id: str
    source: str
    observed_value: str
    supports: Supports
    citation: str
    summary: str


class EvidenceBundle(BaseModel):
    items: list[EvidenceItem]


def _events_by_id(extraction: ExtractionResult) -> dict[str, SoFEvent]:
    return {e.id: e for e in extraction.statement_of_facts.events}


def _supports_from_precip(precip: float) -> Supports:
    # Above threshold -> exception applies -> charterer (time off-hire);
    # below threshold -> exception not met -> owner (time counts).
    if precip > _PRECIP_THRESHOLD_MM_PER_HR:
        return "charterer"
    if precip < _PRECIP_THRESHOLD_MM_PER_HR:
        return "owner"
    return "neutral"


def _weather_item(event_id: str, obs: WeatherObservation) -> EvidenceItem:
    return EvidenceItem(
        event_id=event_id,
        source=obs.source,
        observed_value=f"{obs.precipitation_mm_per_hr} mm/hr",
        supports=_supports_from_precip(obs.precipitation_mm_per_hr),
        citation=f"{obs.source}, {obs.observed_at}",
        summary=(
            f"Precipitation {obs.precipitation_mm_per_hr} mm/hr observed at "
            f"{obs.port} on {obs.observed_at}; CP clause 14 threshold is "
            f"{_PRECIP_THRESHOLD_MM_PER_HR} mm/hr."
        ),
    )


async def gather_evidence(
    extraction: ExtractionResult, dispute: DisputeAnalysis
) -> EvidenceBundle:
    """Return an evidence bundle for the flagged events in ``dispute``.

    Currently handles weather-stoppage events; events for which no tool is yet
    wired or no observation is available are skipped (a stable, non-misleading
    output beats a noisy one).
    """
    sof = extraction.statement_of_facts
    by_id = _events_by_id(extraction)
    items: list[EvidenceItem] = []
    for fe in dispute.flagged_events:
        ev = by_id.get(fe.event_id)
        if ev is None:
            continue
        if ev.category == "stoppage_weather":
            obs = await get_weather(sof.port, ev.timestamp.date().isoformat())
            if obs is not None:
                items.append(_weather_item(fe.event_id, obs))
    return EvidenceBundle(items=items)
