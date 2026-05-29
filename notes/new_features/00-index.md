# Next features - MVP build plans

The top three features to build next, taken from the pitch deck "What's next" slide
and chosen because each is actionable on the current codebase and reuses scaffolding
that already exists. Each doc below breaks the feature into ordered subphases an agent
can build, with concrete file paths and per-phase acceptance.

| # | Feature | One line | Why it is feasible now |
| --- | --- | --- | --- |
| 01 | [Edit with AI](01-edit-with-ai.md) | Select a line in the live claim letter and rewrite it in place, citations preserved. | The reviser micro-agent, safety gate, and `POST /voyages/{id}/revise` route already exist. Mostly wiring + persistence. |
| 02 | [Research agents](02-research-agents.md) | Tool-using agent fetches outside evidence (weather, port calendars) to back each disputed hour. | `FlaggedEvent.evidence_required` is an unused hook; the agent + structured-output helper pattern is established. |
| 03 | [Both sides of the deal](03-both-sides-defense.md) | Defend against an incoming claim, not just file one: a charterer rebuttal with a recomputed quantum. | `Perspective = owner \| charterer` already threads the whole pipeline; `FlaggedEvent` already carries `charterer_argument`. |

## Why not "Live monitoring" yet

The fourth roadmap bullet (connect agents to live voyage and crew updates) was left out
of this set on purpose. It needs external real-time data feeds and an integration with
crew or vessel-tracking systems, which is infrastructure-heavy and not buildable as a
self-contained MVP in a short follow-up window. The three above each ship end to end
against the committed Rotterdam demo voyage.

## Working rules (carry over from notes/15-next-phase.md)

- Branch off `main`; commit after every chunk (shared working tree, uncommitted work has been lost here before).
- `apps/api/portside_api/schemas.py` and `apps/web/lib/types.ts` are FROZEN. Announce before any change. Prefer feature-local wire models (the pattern in `reviser.py`) so the core contract stays untouched.
- Money is never owned by the model. Any euro figure is computed or re-derived in deterministic Python and locked by a test.
- Models: Claude Sonnet 4.6 default, Opus 4.7 via `ANTHROPIC_MODEL_PRIMARY`. Use the shared helpers in `agents/llm.py` and prompt caching.
- No em dashes in prose or generated output.
