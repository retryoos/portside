"""Research tools (A7) — the small set of "outside world" lookups the evidence
agent can call.

For the MVP, ``get_weather`` is backed by a committed offline fixture (sized
to the Rotterdam demo) so the feature works with no network and without an API
key. ``settings.research_live`` reserves the seam to call a real provider later
(e.g., Open-Meteo via httpx, plus geocoding of the port); until that lands, the
fixture path remains the source of truth and the gate stays test-locked.

The tools live in ``agents/`` so future LLM-tool-use plumbing can consume them
directly, but at the moment the researcher calls them deterministically.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..settings import settings


class WeatherObservation(BaseModel):
    port: str
    observed_at: str  # ISO-8601 date
    precipitation_mm_per_hr: float
    wind_knots: float | None = None
    visibility_nm: float | None = None
    source: str


# Committed fixture: the only "outside" datum the Rotterdam demo needs. The 0.2
# mm/hr observation is below CP clause 14's 0.5 mm/hr threshold and is what
# makes the disputed 4h weather stoppage count against the charterer.
_WEATHER_FIXTURE: dict[tuple[str, str], WeatherObservation] = {
    ("Rotterdam", "2026-05-17"): WeatherObservation(
        port="Rotterdam",
        observed_at="2026-05-17",
        precipitation_mm_per_hr=0.2,
        wind_knots=10.0,
        visibility_nm=4.0,
        source="Rotterdam Port Authority weather record",
    ),
}


async def get_weather(port: str, date: str) -> WeatherObservation | None:
    """Return the observation for (port, date), or None when unknown.

    ``settings.research_live`` is honoured as a flag for a future live-API
    implementation; while that seam is unimplemented we always fall back to the
    fixture, so the offline gate stays deterministic.
    """
    if settings.research_live:
        # TODO: live provider (geocode port -> lat/lon, fetch Open-Meteo historical).
        # Until then, fall through to the fixture to keep the feature reliable.
        pass
    return _WEATHER_FIXTURE.get((port, date))
