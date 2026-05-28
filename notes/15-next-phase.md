# Next Phase — Agent 1 & Agent 2 work briefs

> Written after the foundation landed (PR #1) and the demo data was unified (PR #2).
> Grounded in [03-agents.md](03-agents.md), [04-schemas.md](04-schemas.md),
> [02-architecture.md](02-architecture.md), [14-parallel-execution-plan.md](14-parallel-execution-plan.md),
> and [13-inline-revision.md](13-inline-revision.md).

## Where we are now (state of `main`)

- **Backend** (`apps/api`): FastAPI app (`/healthz`, `POST /voyages`, `GET /voyages/{id}`), the **frozen** `VoyageState` Pydantic contract, in-memory store, and a **STUB pipeline** that replays the demo fixture. **No LLM is called yet.**
- **Frontend** (`apps/web`): three screens — `/` (settled case detail), `/claim` (two-column claim view), `/revise` (inline highlight-and-revise) — rendering the demo fixture. Next 15 + Tailwind v4, tokens from `apps/web/DESIGN.md`.
- **Single source of truth** for the demo voyage = **MT Aegean Pioneer, Ras Tanura → Rotterdam, EUR 84,375.00** (72h allowed, 117h used, 45h on demurrage at EUR 1,875/hr; contested 4h weather stoppage on 17 May, CP clause 14 precipitation > 0.5 mm/hr, authority *The Mexico 1* [1990] 1 Lloyd's Rep 507). Lives in `apps/web/DESIGN.md` = `apps/web/lib/demo.ts` = `apps/api/portside_api/fixtures.py`. **Do not reintroduce the old Athens/Piraeus/38,400 scenario.**

The headline gap: **the pipeline is a stub.** The next phase is making `POST /voyages` run the real four-agent fleet over uploaded PDFs.

## Working rules (both agents)

- Branch off `main`; **commit after every chunk** — this is a shared working tree and uncommitted work has been lost here before. Bundle into the hackathon's single-PR flow.
- Confirm **Entire** is enabled (`entire status` → ENABLED) before coding; run `entire dispatch` near submission (judging requirement, see [12-runbook.md §1c](12-runbook.md)).
- `schemas.py` / `apps/web/lib/types.ts` are **FROZEN** — announce before any change.
- Models: **Sonnet 4.6** default, Opus 4.7 escape via env. Prompt caching on the CP text, tool-use `strict: true`. Use the `claude-api` skill. See [11-prompts.md](11-prompts.md).
- Stay in your lane (file lists below) so the two agents never collide.

---

## Agent 1 — Backend pipeline: ingestion + calculation (Track A)

**Goal:** replace the stub so `POST /voyages` runs Agent 1 + Agent 2 over the uploaded PDFs and returns a real `VoyageState`.

**Build:**
- `apps/api/portside_api/pdf.py` — `extract_pdf_text(pdf_bytes) -> str` using `pdfplumber` (text + tables), per [03-agents.md "PDF text extraction"](03-agents.md). Fallback to a Claude `document` block only if extraction is empty.
- `apps/api/portside_api/agents/extractor.py` — **Agent 1**: one Sonnet 4.6 tool-use (`strict`) call over the three text blobs → `ExtractionResult`. Prompt in `apps/api/portside_api/prompts/extractor.md`.
- `apps/api/portside_api/agents/calculator.py` — **Agent 2a** LLM classifier (one call → `list[EventClassification]`) **and** **Agent 2b** deterministic Python `calculate_laytime(...) -> LaytimeResult` (the LLM never does arithmetic). Prompt in `prompts/classifier.md`.
- `apps/api/tests/test_calculator.py` — **the gate.** Lock the arithmetic to the Rotterdam worked example (72 / 117 / 45h → **EUR 84,375.00** at 1,875/hr). Do not merge if this fails.
- `synthetic-data/` — generate the Rotterdam demo PDFs (CP, NOR, SoF) + `expected.json`, reconciling to EUR 84,375. `weasyprint`, **dev-time only** (never in the runtime/App Runner image).
- Wire `apps/api/portside_api/pipeline.py`: `pdfplumber → extractor → calculator`, updating `VoyageState` **per stage** (keep the staged `extracting/calculating/...` updates so the UI's AgentSteps animate). Leave a clean seam for Agent 2's analyst+drafter in the `asyncio.gather`.

**Acceptance:** upload the synthetic PDFs → `GET /voyages/{id}` progresses to `done` with real `extraction` + `laytime`; `test_calculator.py` passes; quantum on the demo PDFs is EUR 84,375.00.

**Do NOT touch:** `apps/web/*`, `agents/analyst.py`, `agents/drafter.py` (Agent 2's lane).

---

## Agent 2 — Reasoning, drafting + live frontend wiring (Track B + C bridge)

**Goal:** produce the real `DisputeAnalysis` + `ClaimPacket`, and make the UI run on the **live pipeline** instead of the static demo fixture.

**Build:**
- `apps/api/portside_api/agents/analyst.py` — **Agent 3**: Sonnet 4.6, `ExtractionResult` + `LaytimeResult` + contestable classifications → `DisputeAnalysis` (clause + event-ID citations; `owner_position_strength`). Prompt in `prompts/analyst.md`. Per [03-agents.md "Agent 3"](03-agents.md).
- `apps/api/portside_api/agents/drafter.py` — **Agent 4**: **streamed** BIMCO claim letter + dispute narrative → `ClaimPacket`. Template `apps/api/portside_api/letter_template.html`, prompt `prompts/drafter.md`.
- **Frontend live wiring** (`apps/web`): an upload entry (dropzone) that calls `createVoyage` + `pollVoyage` (already in `apps/web/lib/api.ts`) and feeds the live `VoyageState` into the existing screens, which today read `apps/web/lib/demo.ts`. Keep "Try the demo voyage" as the offline fallback. Drive the `/claim` stage/progress UI off the polled `stage`.
- **(Stretch)** inline-revise backend per [13-inline-revision.md](13-inline-revision.md) (`agents/reviser.py` + a `/revise` route) to back the `/revise` screen.

**Acceptance:** live upload → `/claim` shows the real letter, dispute, and quantum (streamed); the offline demo still works.

**Coordinate:** Agent 1 owns `pipeline.py`; you plug `analyst` + `drafter` into its `asyncio.gather` (run Agent 3 ∥ Agent 2, Agent 4 awaits both — see [02-architecture.md §6](02-architecture.md)).

**Do NOT touch:** `agents/extractor.py`, `agents/calculator.py`, `pdf.py` (Agent 1's lane).

---

## Shared references

- Concurrency + latency budget: [02-architecture.md §5–6](02-architecture.md).
- Output schemas + worked example: [04-schemas.md](04-schemas.md).
- Prompt rules + cross-cutting AI-tell suppression: [11-prompts.md](11-prompts.md).
- Demo script the pipeline must satisfy: [08-demo-and-pitch.md](08-demo-and-pitch.md).
