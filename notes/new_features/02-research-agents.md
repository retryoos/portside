# Feature 02 - Research agents (tool-using evidence gathering)

## Goal

Add a research agent that, for each contested window in the dispute, calls real tools to
fetch independent outside evidence (weather observations for the port and date, port
working calendars and holidays) and attaches it to the claim, so every disputed hour is
backed by an external source rather than the documents alone. The evidence then shows up
in the letter, in the supporting-documents list, and in a new Evidence tab.

## Why it matters

This is the agentic-AI beat of the roadmap (giving the Claude agents tools and skills).
It fills `FlaggedEvent.evidence_required`, a field that already lists what evidence each
contested point needs but which nothing currently fetches. Independently sourced evidence
is exactly what makes a contested hour defensible to a counterparty.

## What already exists (reuse, do not rebuild)

- `apps/api/portside_api/schemas.py`: `FlaggedEvent.evidence_required: list[str]` is the
  hook. The analyst already populates it.
- `apps/api/portside_api/agents/llm.py`: shared `AsyncAnthropic` client, `cached_system`,
  and `extract_structured(...)`. The same client supports the tool-use loop.
- `apps/api/portside_api/agents/analyst.py`: produces `flagged_events`. The research agent
  runs after the analyst.
- `apps/api/portside_api/pipeline.py`: staged orchestrator with a clean seam to insert a
  new stage and an `emit(...)` helper for live polling.
- `apps/web/components/SourcesTabs.tsx`: where a new Evidence tab belongs.
- The committed Rotterdam scenario: the contested point is a 4 hour weather stoppage on
  17 May, CP clause 14 (precipitation > 0.5 mm/hr threshold not met). The evidence tool
  should corroborate that the rain did not meet the threshold.

## Design notes

- Keep the tools real but demo-safe. Ship a committed local fixture tool first so the demo
  works offline, with a settings-flagged seam to call a live API later.
- Use the Anthropic tool-use loop: define the tools, let the model decide which contested
  points need which evidence, return tool results, then collect a structured result.
- Money stays deterministic. Evidence may adjust a qualitative strength, never a euro
  figure directly.

## Subphases

### Phase 0 - Tool layer
Create `apps/api/portside_api/agents/tools.py`:
- `get_weather(port: str, date: str) -> WeatherObservation` returning precipitation
  mm/hr, wind, and visibility. Back it with a committed fixture for the Rotterdam 17 May
  scenario (precipitation < 0.5 mm/hr). Add a `settings`-flagged branch to call a free
  historical weather API (for example Open-Meteo) when enabled.
- (optional) `get_port_calendar(port: str, date: str) -> PortDay` returning whether the
  day is a holiday or non-working, from a small committed table.
Acceptance: `get_weather("Rotterdam", "2026-05-17")` returns the fixture value offline.

### Phase 1 - The research agent
Create `apps/api/portside_api/agents/researcher.py` with `run(extraction, dispute) ->
EvidenceBundle`. It runs the tool-use loop over the flagged events and returns a
feature-local `EvidenceBundle` (defined in this module, not in frozen `schemas.py`):
`EvidenceBundle { items: list[EvidenceItem] }`, where
`EvidenceItem { event_id, source, observed_value, supports: "owner"|"charterer"|"neutral",
citation, summary }`. Prompt: `apps/api/portside_api/prompts/researcher.md`.
Acceptance: on the Rotterdam fixture, the agent returns an item for the weather-stoppage
event whose `observed_value` reflects the sub-threshold precipitation.

### Phase 2 - Pipeline wiring
Insert a `researching` stage in `pipeline.py` between `analyzing` and `drafting` so the UI
animates it. Adding `"researching"` to `PipelineStage` is a frozen-schema change: announce
it first. Feed the `EvidenceBundle` into the drafter so the letter and
`supporting_documents` cite the external source.
Acceptance: a live run emits `researching`, then `drafting`, then `done`, and the letter
references the weather evidence.

### Phase 3 - Strength re-rating (deterministic)
Adjust `FlaggedEvent.owner_position_strength` from the evidence in plain Python (for
example, corroborating evidence nudges strength up, contradicting evidence nudges it
down), with clamped bounds. The model does not set the final number.
Acceptance: corroborated weather evidence raises the owner strength on that flag.

### Phase 4 - Frontend Evidence tab
Add an Evidence panel to `SourcesTabs.tsx` listing each `EvidenceItem` with its source,
observed value, who it supports, and a link. Persisting the bundle to the frontend needs
an additive field on the state; if you add it to `VoyageState`, announce the frozen-schema
change, otherwise thread it through the packet for MVP.
Acceptance: the Evidence tab shows the weather item on the Rotterdam case.

### Phase 5 - Tests
Lock the fixture tool: `get_weather("Rotterdam", "2026-05-17")` returns sub-threshold
precipitation, and the bundle marks the 4 hour stoppage as not qualifying under clause 14.
Acceptance: tests pass without an API key (tool fixture path), calculator gate untouched.

## MVP acceptance (end to end)

Running the Rotterdam demo produces an Evidence item for the 17 May weather stoppage drawn
from the weather tool, the dispute narrative cites it by source, and it appears in an
Evidence tab. The whole thing works offline via the fixture; the live API path is behind a
settings flag.

## Do NOT touch

The deterministic calculator math. Any euro figure stays computed in Python. Announce
before changing `schemas.py` (the `researching` stage and any new `VoyageState` field).

## Out of scope for MVP

Real-time or live feeds, contacting crew, multiple competing data providers, a caching or
rate-limit layer, and evidence for anything beyond the flagged contested windows.
