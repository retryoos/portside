# Branch state — May 28th

> Single source of truth for who is working on what.
> Update your own row whenever you push / open a PR / merge.
> See notes/14-parallel-execution-plan.md §11 for the schema.

| Status | Branch | Owner | What | PR |
| ------ | ------ | ----- | ---- | -- |
| [MERGED 11:30] | `agent-1/ingestion-calc` | Agent 1 | Track A — pdf.py, extractor, calculator (2a + 2b), gate test, synthetic data, pipeline wiring | #4 |
| [WIP]          | `agent-2/...`            | Agent 2 | Track B + C — analyst, drafter, letter template, frontend live wiring to createVoyage/pollVoyage, stretch revise route | (pending) |
| [WIP]          | `agent-3/track-d-foundation` | Agent 3 | Track D — settings, cross-cutting prompt, deploy artifacts, async-background POST + store.patch(), offline demo fixture, doc cleanups, smoke script | (pending) |

## Lane reminders

- Schemas (`apps/api/portside_api/schemas.py`, `apps/web/lib/types.ts`) are FROZEN — announce before any change.
- `apps/api/portside_api/pipeline.py` — Agent 2 owns active edits (plug analyst+drafter into the SEAM). Track D published the staged-update contract via `store.patch()`.
- `apps/api/portside_api/main.py` — Track D refactored to async-background. Agent 2 likely will not need to touch this.
- `apps/web/lib/demo.ts` — Agent 2 owns. Track D's offline fixture (`apps/web/public/demo-fixture.json`) is an alternative path, not a replacement.
- Both Anthropic API spend AND any live smoke run remain GATED behind explicit user authorisation (Track D writes test mocks and an unrun smoke script for this reason).
