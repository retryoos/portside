# Parallel Execution Plan — agent-fleet subphases

> The companion to [07-day-plan.md](07-day-plan.md) and [10-ai-fleet-playbook.md](10-ai-fleet-playbook.md). Those describe the day at engineer-grain. **This doc describes the day at subagent-grain**, with explicit branch-per-subphase assignments so the fleet can fan out in parallel on isolated worktrees and merge to `main` in a defined order.
>
> Read this together with [09-pre-merge-protocol.md](09-pre-merge-protocol.md). Branches still merge through the four pre-merge checks; this doc only changes **what** branches exist and **who/what** drives them.

---

## 1. The fleet, updated for May 28

Reconciles [10-ai-fleet-playbook.md §1](10-ai-fleet-playbook.md#1-the-fleet) with the current seat list:

| # | Seat                | Tier             | Role on the day                                      |
| - | ------------------- | ---------------- | ---------------------------------------------------- |
| 1 | dkall (main gmail)  | Claude **Max**   | Anchor — Track A driver, multi-session capable        |
| 2 | Roman               | Claude **Max**   | Track C driver, multi-session capable                 |
| 3 | Panos               | Claude **Pro**   | Track B driver                                        |
| 4 | Stamatis            | Claude **Pro**   | **Backup** — failover seat for rate-limit hits         |
| 5 | Reserve #1 (Pro)    | Claude **Pro**   | Creatable on demand (gmail alias)                     |
| 6 | Reserve #2 (Pro)    | Claude **Pro**   | Creatable on demand (gmail alias)                     |
| 7 | Glacdimitris        | Gemini Pro       | Cross-check, red-team, second-opinion                 |
| C1| Cursor on dkall #1  | (paid seat)      | Background subagent — synthetic data                  |
| C2| Cursor on dkall #2  | (paid seat)      | Background subagent — letter/template polish          |
| C3| Cursor on Roman     | (paid seat)      | Background subagent — frontend polish / impeccable    |
| C4| Cursor on Panos     | (paid seat)      | Background subagent — prompt iteration                |

**Effective concurrency:** up to **2 Max + 2 Pro + 4 Cursor + 1 Gemini = 9 concurrent AI sessions** with 2 more Pros in reserve. Practical limit is human supervision, not seats — each human can productively supervise ~3 concurrent sessions before integration cost outweighs gain. So plan for **~7–8 truly parallel branches at peak**.

> **Critical update:** [10-ai-fleet-playbook.md §1](10-ai-fleet-playbook.md#1-the-fleet) lists Roman as Pro and Stamatis as primary. That doc was written before the Max upgrade. Treat this section as the authoritative seat list.

---

## 2. Subphase = one branch, one PR, ≤90 min, one self-contained surface

A **subphase** is the unit of fan-out. To qualify it must:

- Live on **its own branch** off the latest `main`.
- Touch a **disjoint set of files** from every other concurrent subphase (so two branches never collide on merge).
- Be **shippable in 30–90 minutes** by one driver + their subagents.
- Pass the **four pre-merge checks** in [09-pre-merge-protocol.md §2](09-pre-merge-protocol.md#2-the-four-pre-merge-checks-every-pr) before merging.
- Be either **self-verifiable** (the smoke test in the PR proves it works) or **buildable against a fixture** (so it doesn't block on another subphase finishing).

If a piece of work doesn't qualify, it's either too big (split it) or too entangled (sequence it after the integration window).

---

## 3. The wave structure

```
Wave 0  ─ Foundation (BLOCKING, ~30–45 min, sequential, one driver)
   │
   ▼
Wave 1  ─ Parallel build fan-out (~12 branches, ~60–90 min)
   │
   ▼
Wave 2  ─ Integration smoke (sequential, ~30 min)
   │
   ▼
Wave 3  ─ Stretch tier 1 fan-out (~5 branches, ~60–90 min)
   │
   ▼
Wave 4  ─ Polish, freeze, demo prep (sequential, 17:30 → 19:00)
```

Each wave merges to `main` before the next opens. Within a wave, branches merge in any order (the disjoint-files rule guarantees no conflicts).

---

## 4. Wave 0 — Foundation (09:45 – 10:30, blocking)

**Goal:** Wave 1 fan-out can't start until these files exist on `main`.

One driver (recommend **dkall, Track A**) does this in one fast push. Everyone else **reads the docs they own** and **provisions their second Claude/Cursor session** during this window — they do not branch yet.

Single branch: **none** — Wave 0 commits go straight to `main` (it's the only window where this is allowed, because there is nothing yet to break).

| Subphase | File(s) created                                                                                                          | Driver       |
| -------- | ------------------------------------------------------------------------------------------------------------------------ | ------------ |
| 0a       | `apps/api/pyproject.toml`, `apps/api/portside_api/{__init__.py,main.py}` — FastAPI hello-world, `/healthz`, CORS         | dkall        |
| 0b       | `apps/api/portside_api/schemas.py` — all Pydantic models from [04-schemas.md](04-schemas.md), **complete**, **frozen**   | dkall        |
| 0c       | `apps/api/portside_api/storage.py` — `VoyageStore` Protocol + `InMemoryStore`                                            | dkall        |
| 0d       | `apps/api/portside_api/pipeline.py` — orchestrator stub that returns a hard-coded `VoyageState` fixture                  | dkall        |
| 0e       | `apps/api/portside_api/main.py` — `POST /voyages`, `GET /voyages/{id}` returning the fixture                             | dkall        |
| 0f       | `apps/web/package.json`, `apps/web/app/{layout.tsx,page.tsx}`, `apps/web/app/theme.css` (exported from `DESIGN.md`)      | Roman (parallel) |
| 0g       | `apps/web/lib/{api.ts,types.ts}` — typed fetch client + zod types mirroring `schemas.py`                                 | Roman (parallel) |
| 0h       | `apps/api/.env.example`, `apps/web/.env.example`                                                                          | dkall        |
| 0i       | `notes/fleet-assignments.md` — written record of who owns what for the day                                                | Panos        |

0a–0e and 0h commit straight to `main` from dkall. 0f–0g commit straight to `main` from Roman. **Both end before 10:30.** No PRs. After 10:30 the rest of the day is PR-only.

**Acceptance:** `curl localhost:8000/voyages/v_test` returns the fixture VoyageState; `pnpm dev` renders the three-panel layout against that fixture.

---

## 5. Wave 1 — Parallel fan-out (10:30 – 13:00)

Twelve branches, all branched off `main` at the Wave 0 merge point. None of them touch the same file as any other (see file table in §10 for proof). Every branch is **buildable against fixtures** — none waits for another to finish.

### Branch list

| # | Branch                            | Owner driver | Subagent helpers                  | Primary files touched                                                                                  | Verification                                              |
| - | --------------------------------- | ------------ | --------------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| 1a| `track-a/agent1-extractor`        | dkall        | Cursor C1 (Explore PDF parsing)   | `agents/extractor.py`, `prompts/extractor.md`, `prompts/cross_cutting.md`                              | unit: call against a fixture text → returns `ExtractionResult` |
| 1b| `track-a/agent2-classifier`       | dkall        | —                                 | `agents/calculator.py` (LLM 2a only), `prompts/classifier.md`                                          | unit: classify a fixture extraction → list[EventClassification] |
| 1c| `track-a/agent2-arithmetic`       | dkall        | Cursor C1 (test cases)            | `agents/calculator.py` (Python 2b), `tests/test_calculator.py`                                          | pytest passes with worked-example numbers from [04-schemas.md §8](04-schemas.md#8-worked-example-values-use-these-in-tests-and-fixtures) |
| 1d| `track-b/agent3-analyst`          | Panos        | Cursor C4 (prompt iteration)      | `agents/analyst.py`, `prompts/analyst.md`                                                              | unit: against fixture LaytimeResult → DisputeAnalysis |
| 1e| `track-b/agent4-drafter`          | Panos        | Cursor C2 (letter template)       | `agents/drafter.py`, `prompts/drafter.md`, `letter_template.html`                                       | unit: against fixture inputs → ClaimPacket with letter_markdown |
| 1f| `track-b/exports`                 | Panos        | —                                 | `routes/exports.py` (weasyprint + python-docx endpoints)                                               | curl `/letter.pdf` returns a valid PDF |
| 1g| `track-c/skeleton-tokens`         | Roman        | Cursor C3 (impeccable shape)      | `app/globals.css`, `app/theme.css` extension, `components/Topbar.tsx`, `components/TimebarBadge.tsx`    | renders cleanly at desktop + mobile breakpoints |
| 1h| `track-c/left-panel-docs`         | Roman        | —                                 | `components/{Dropzone,DocumentCard}.tsx`, `app/voyages/[id]/LeftPanel.tsx`                              | drag-drop fires POST; cards render from fixture |
| 1i| `track-c/center-panel-laytime`    | Roman        | Cursor C3 (impeccable layout)     | `components/{AgentSteps,LaytimeTable,QuantumDisplay,ContestedExpansion}.tsx`, `CenterPanel.tsx`         | renders against fixture; contested-row click expands |
| 1j| `track-c/right-panel-claim`       | Roman        | —                                 | `components/{ExecutiveSummary,DisputeNarrative,LetterPreview}.tsx`, `RightPanel.tsx`                    | renders against fixture; download button fires |
| 1k| `data/scenarios`                  | dkall (own Cursor C1) | own — runs autonomously   | `synthetic-data/generate.py`, `synthetic-data/scenarios/athens-weather-dispute/*`                       | 3 PDFs + `expected.json` exist; numbers reconcile to EUR 38,400 |
| 1l| `track-a/pipeline-wiring`         | dkall        | —                                 | `pipeline.py` (wire real agents in, with `asyncio.gather` for 2+3)                                      | end-to-end pipeline against synthetic data returns full VoyageState |

> **Lane discipline:** 1l (`pipeline-wiring`) is the **last** Wave-1 branch to open. It is the integration of 1a + 1b + 1c + 1d + 1e against the data from 1k. It must wait until at least 1a, 1c, 1k have landed. Treat it as a "wave 1.5" — start it at 12:00, not 10:30.

### Worktree strategy

Each driver uses `git worktree` to keep concurrent branches on separate directories on the same laptop:

```bash
# from inside ~/Desktop/Code/FlorentHackathon/Source (the primary worktree on main)
git worktree add ../wt-agent1     track-a/agent1-extractor
git worktree add ../wt-agent2-arith track-a/agent2-arithmetic
git worktree add ../wt-data       data/scenarios
```

Each worktree has its own Claude/Cursor session pointed at it. **Never run two Claude sessions in the same worktree.** Worktrees are deleted on merge:

```bash
git worktree remove ../wt-agent1
```

This is also how Cursor stays untangled — each Cursor seat opens a different worktree path.

### Account → branch assignment (recommended)

| Seat                | Wave 1 branches owned                                | Notes                                                            |
| ------------------- | ---------------------------------------------------- | ---------------------------------------------------------------- |
| dkall (Max) primary | `track-a/agent1-extractor`, `track-a/agent2-classifier`, `track-a/agent2-arithmetic`, `track-a/pipeline-wiring` | Sequential within worktree; arithmetic is the test-locked one    |
| dkall (Max) side    | spawn subagent for `track-a/agent1-extractor` while typing `track-a/agent2-arithmetic` | Max supports parallel sessions; use a second worktree           |
| Roman (Max) primary | `track-c/skeleton-tokens`, `track-c/center-panel-laytime`     | Center panel is the high-value frontend surface                  |
| Roman (Max) side    | `track-c/left-panel-docs`, `track-c/right-panel-claim`        | Second worktree, second `claude` session                         |
| Panos (Pro)         | `track-b/agent3-analyst`, `track-b/agent4-drafter`, `track-b/exports` | Sequential — analyst → drafter → exports                         |
| Cursor C1 (dkall)   | `data/scenarios` (B1 brief from [10-ai-fleet-playbook.md §5](10-ai-fleet-playbook.md#b1--synthetic-data-factory-paste-at-1000)) | Long-running autonomous; check-ins via `STATUS.md` |
| Cursor C2 (dkall)   | (held in reserve until Wave 3 inline-revise)         | Or assist Panos's `track-b/agent4-drafter` letter polish if free |
| Cursor C3 (Roman)   | `/impeccable` audit pass on each track-c branch before merge | Reactive — runs against each Track C PR diff                     |
| Cursor C4 (Panos)   | Prompt iteration loop (B2 brief from [10-ai-fleet-playbook.md §5](10-ai-fleet-playbook.md#b2--prompt-iteration-paste-at-1200)) | Long-running autonomous; appends to `notes/prompt-iteration-log.md` |
| Glacdimitris (Gemini)| Reactive — X1 cross-check at 13:00, 15:00, 17:30, 18:30 | Capture in `notes/cross-check-log.md` |
| Stamatis (Pro backup)| Idle. Spin up on the first rate-limit hit.            | Inherits whichever account stalled                                |

**Merge order within Wave 1:** any order, except `track-a/pipeline-wiring` lands last.

### Subagent-vs-new-session decision tree

When the driver of a branch wants to delegate a piece of work:

```
Is it a self-contained 5–20 min task with a narrow scope (grep, file edit, test write)?
  └── YES → spawn an Agent subagent in the same session (Explore for read-only, general-purpose otherwise)
  └── NO  → is it a long-running autonomous workstream (>30 min, periodic check-in)?
        └── YES → open a separate Cursor/Claude session in a separate worktree
        └── NO  → do it yourself; the orchestration overhead exceeds the saving
```

The Agent tool is for **delegating within a session** (one subagent at a time per parent). Cursor/separate-session is for **truly concurrent workstreams** (the data factory running for 2 hours while you build agents).

---

## 6. Wave 2 — Integration smoke (13:00 – 14:00, sequential)

After lunch. Demo-laptop owner runs the full end-to-end on the demo laptop. **Five-minute drill, no new feature branches open.**

1. `git checkout main && git pull`
2. `cd apps/api && uv sync && uv run uvicorn portside_api.main:app --port 8000` — boots
3. `cd apps/web && pnpm install && pnpm dev` — boots
4. Browser: drag the three demo PDFs onto the dropzone
5. Watch all four agents step through; quantum populates; letter generates
6. Report PASS or capture the first failure point

If FAIL, the team huddles for 60s and opens a single `fix/wave-1-integration` branch. The driver who owns the failing surface fixes it; everyone else **does not branch** during the integration fix.

This window is also when [09-pre-merge-protocol.md §3](09-pre-merge-protocol.md#3-integration-checkpoints-full-end-to-end-all-three-tracks)'s 13:00 checkpoint happens. Combine them.

---

## 7. Wave 3 — Stretch tier 1 fan-out (15:30 – 17:30)

Conditional on the 15:00 mentor check-in returning a green-ish read. If we are not green, defer Wave 3 and use the time to polish Wave 1's surfaces.

Branches, all parallel:

| # | Branch                              | Owner driver | Files                                                                                | Tier 1 ref                                  |
| - | ----------------------------------- | ------------ | ------------------------------------------------------------------------------------ | ------------------------------------------- |
| 3a| `stretch/inline-revise-backend`     | dkall        | `agents/reviser.py`, `prompts/reviser.md`, `routes/revise.py`, `schemas.py` (add `TextSegment`, `Revision`, extend `ClaimPacket`) | [13-inline-revision.md §4 + §5](13-inline-revision.md#4-backend--the-revision-endpoint) |
| 3b| `stretch/inline-revise-frontend`    | Roman        | `components/{RevisableSurface,SegmentSpan,RevisionToolbar,RevisionPanel,EditedBadge}.tsx`, `hooks/useTextSelection.ts` | [13-inline-revision.md §6](13-inline-revision.md#6-frontend--the-components) |
| 3c| `stretch/charterer-toggle`          | Panos        | `agents/analyst.py` (already param), `Topbar.tsx` toggle wiring, `lib/api.ts`         | [extended_plan.md §9 Tier 1.2](extended_plan.md#tier-1--if-we-finish-the-mvp-by-1530) |
| 3d| `stretch/timebar-red`               | Roman (Cursor C3) | `components/TimebarBadge.tsx` — color logic                                          | [extended_plan.md §9 Tier 1.3](extended_plan.md#tier-1--if-we-finish-the-mvp-by-1530) |
| 3e| `stretch/excel-export`              | Panos        | `routes/exports.py` (add openpyxl endpoint), button on `RightPanel`                  | [extended_plan.md §9 Tier 1.4](extended_plan.md#tier-1--if-we-finish-the-mvp-by-1530) |

> **Schema-change rule:** 3a is the only Wave-3 branch that touches `schemas.py`. 3a freezes the new `TextSegment` shape **by 15:45** and announces in chat so 3b can mirror it in `types.ts`. After 15:45, schema is frozen again until 18:00.

**Merge order within Wave 3:** 3a + 3b first (they enable Beat 5.5); others fold in afterwards. If any branch isn't landing by 17:00, cut it per [13-inline-revision.md §8](13-inline-revision.md#8-cut-order-if-behind-on-stretch).

---

## 8. Wave 4 — Polish, freeze, demo prep (17:30 – 19:00)

No new branches. Everything happens on `main` or on `fix/*` micro-branches.

| Time          | Action                                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------------------ |
| 17:30         | Feature freeze. Two dress rehearsals on the demo laptop. Gemini X1 final pass via Glacdimitris.              |
| 17:30 – 18:00 | Demo polish per [06-frontend.md §10](06-frontend.md#10-the-demo-polish-list). Cursor C3 runs `/impeccable polish` on every surface. |
| 18:00 – 18:30 | Record backup video. Save `apps/web/public/demo-fixture.json`. Stage demo PDFs on desktop.                    |
| 18:30 – 19:00 | Demo lock. Only the demo-laptop owner touches keys. Other engineers prep pitch slides and Q&A in [08-demo-and-pitch.md §2](08-demo-and-pitch.md#part-2--anticipated-judge-questions). |

---

## 9. Conflict avoidance — the disjoint-files matrix

Wave 1's twelve branches were designed to never overlap on the same file. Verification table:

| File / dir                                      | Owned by branch(es) (Wave 1)                                                                       |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `apps/api/portside_api/schemas.py`              | **FROZEN** — no Wave 1 branch touches it                                                            |
| `apps/api/portside_api/agents/extractor.py`     | 1a only                                                                                            |
| `apps/api/portside_api/agents/calculator.py`    | 1b (LLM half), 1c (Python half) — split via function boundary; 1c merges first, 1b appends         |
| `apps/api/portside_api/agents/analyst.py`       | 1d only                                                                                            |
| `apps/api/portside_api/agents/drafter.py`       | 1e only                                                                                            |
| `apps/api/portside_api/prompts/*.md`            | one file per branch; no file shared                                                                |
| `apps/api/portside_api/letter_template.html`    | 1e only                                                                                            |
| `apps/api/portside_api/routes/exports.py`       | 1f only                                                                                            |
| `apps/api/portside_api/pipeline.py`             | 1l only (wired last)                                                                               |
| `apps/api/tests/test_calculator.py`             | 1c only                                                                                            |
| `apps/web/app/globals.css` / `theme.css`        | 1g only                                                                                            |
| `apps/web/components/Topbar.tsx` / `TimebarBadge.tsx` | 1g only                                                                                        |
| `apps/web/components/{Dropzone,DocumentCard}.tsx` + `LeftPanel.tsx`  | 1h only                                                              |
| `apps/web/components/{AgentSteps,LaytimeTable,QuantumDisplay,ContestedExpansion}.tsx` + `CenterPanel.tsx` | 1i only                                              |
| `apps/web/components/{ExecutiveSummary,DisputeNarrative,LetterPreview}.tsx` + `RightPanel.tsx` | 1j only                                                                 |
| `apps/web/lib/{api.ts,types.ts}`                | Wave 0 only (frozen); changes in Wave 3 (3a/3b) only                                                |
| `synthetic-data/*`                              | 1k only                                                                                            |

> **The only file that two branches need to coordinate on is `calculator.py`**, because 1b and 1c both live in it. Mitigation: 1c lands first (it has the test); 1b adds the LLM classifier *function* above the existing arithmetic without renaming anything. If you need belt-and-braces, split into `calculator.py` (Python) and `classifier.py` (LLM) at Wave 0 — recommended.

---

## 10. Mapping back to [07-day-plan.md](07-day-plan.md)

[07-day-plan.md](07-day-plan.md) describes the day at engineer-grain (Track A / B / C). This doc decomposes each Track's work into Wave-1 branches. The hour-by-hour mapping:

| Time          | [07-day-plan.md](07-day-plan.md) hour       | Wave from this doc                            |
| ------------- | ------------------------------------------- | --------------------------------------------- |
| 09:45 – 10:45 | Hour 1 — Skeletons + contract freeze        | **Wave 0** (compresses to 30–45 min; remainder used for first Wave-1 branch openings) |
| 10:45 – 11:45 | Hour 2 — Agent 1 + UI panels v1             | Wave 1 branches 1a, 1g, 1h in active build     |
| 11:45 – 13:00 | Hour 3 — Agent 2 arithmetic + Agent 3       | Wave 1 branches 1b, 1c, 1d, 1i, 1k landing    |
| 13:00 – 14:00 | Lunch                                       | **Wave 2** integration smoke happens at 13:00 before lunch |
| 14:00 – 15:00 | Hour 4 — Agent 4 + letter export            | Wave 1 branches 1e, 1f, 1j, 1l landing         |
| 15:00 – 15:15 | Hour 5 — Mentor check-in                    | Pause Wave 1 closure                           |
| 15:15 – 16:30 | Hour 6 — Polish round 1                     | **Wave 3** opens                               |
| 16:30 – 17:30 | Hour 7 — Backup scenarios + edge cases      | Wave 3 closes                                  |
| 17:30 – 18:30 | Hour 8 — Freeze + dress rehearsal #2        | **Wave 4** opens                               |
| 18:30 – 19:00 | Hour 9 — Submission + freshen up            | Wave 4 close                                   |

If any wave runs late, the slack comes out of the next wave's stretch budget, not out of demo prep. **Demo prep is non-negotiable from 18:00.**

---

## 11. Single source of truth for branch state

Maintain `notes/branch-state.md` (committed, updated live by whichever engineer just merged) with one line per branch:

```
- [DONE 11:34] track-a/agent1-extractor — dkall — merged to main
- [WIP  12:10] track-c/center-panel-laytime — Roman — agent steps wired, table renders fixture
- [BLOCKED] data/scenarios — Cursor C1 — weasyprint cairo dep missing on dkall laptop, see UNBLOCK_ME.md
```

This is the team's status board. No Slack thread, no chat, no whiteboard. A single committed file. Five seconds to update; saves all the "where are you" overhead.

---

## 12. What we will NOT parallelise

- **Schemas changes.** One author, one merge, announce verbally before opening the PR. Schema PRs do not run in parallel with anything that consumes the schema.
- **The orchestrator (`pipeline.py`).** One author for all of Wave 1 (1l). Anyone touching it during Wave 3 (e.g., adding the revise route) coordinates with dkall.
- **`main` during the integration smoke (Wave 2)** and the freeze (Wave 4). All branches paused.
- **The demo laptop.** From 17:30 onward, one owner. Other engineers can keep coding on their own laptops, but the demo laptop's `main` is read-only.

---

## 13. Cheat sheet — what to do right now

If you are reading this for the first time on May 28 morning:

1. **Open this doc + [07-day-plan.md](07-day-plan.md) + [09-pre-merge-protocol.md](09-pre-merge-protocol.md) on your second monitor.** Keep them visible all day.
2. **Find your name in §5's account → branch table.** That is the queue of branches you own today.
3. **Set up your worktrees.** One worktree per branch you'll work on concurrently. Open each in its own terminal + Claude session.
4. **At 10:30** (Wave 0 done) — `git pull main` in every worktree, branch off, start the first subphase.
5. **At each merge** — update `notes/branch-state.md` with the timestamp, push, move to the next branch.
6. **At 13:00, 15:00, 17:30** — drop everything for the 5-minute checkpoint per [09-pre-merge-protocol.md §3](09-pre-merge-protocol.md#3-integration-checkpoints-full-end-to-end-all-three-tracks).

The whole day is paying attention to two things: **your branch queue** and **the checkpoints**. Everything else is noise.
