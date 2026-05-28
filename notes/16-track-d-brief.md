# Track D — Foundation, async plumbing, deploy & demo readiness

> The third PR alongside Agent 1's `agent-1/ingestion-calc` (merged as #4) and
> Agent 2's pending Track B + frontend wiring branch. This PR is strictly disjoint
> in file ownership from both — see §"Lane discipline" below.

## What this PR landed

Six commits on `agent-3/track-d-foundation`, all pure-Python plumbing or static
config. No live LLM calls in any commit, in any test, in any script. Calculator
gate (`tests/test_calculator.py`) still passes; new tests bring the suite to 33
green.

| # | Commit | What it adds |
| - | ------ | ------------ |
| 1 | `Track D: settings module — env-driven config + .env loader` | `portside_api/settings.py` + `.env.example` + 9 tests. Stdlib-only `Settings.load()` reading `ANTHROPIC_API_KEY` / model selectors / `REQUEST_TIMEOUT_S` / `CORS_ORIGINS`. Existing `os.environ` reads in `agents/llm.py` untouched. |
| 2 | `Track D: cross-cutting prompt prefix + load_prompt() helper` | `portside_api/prompts/__init__.py` (`load_prompt(name)`, lru-cached) + `portside_api/prompts/cross_cutting.md` (verbatim from `notes/11-prompts.md`, anchored to USD 84,375). 6 tests including a vocab-marker guard. |
| 3 | `Track D: deploy artifacts (Dockerfile, App Runner, Amplify) + deploy runbook` | `apps/api/Dockerfile` (python:3.12-slim + uv, no native deps), `.dockerignore`, `apprunner.yaml`, `apps/web/amplify.yml` (npm-based to match the committed lockfile), `notes/16-aws-deploy.md`. |
| 4 | `Track D: async-background POST /voyages + store.patch() contract` | `main.py` POST now seeds `stage="uploaded"`, spawns `asyncio.create_task(pipeline.run(...))` with a strong-ref `set`, returns immediately. `VoyageStore.patch(voyage_id, **fields)` added with `asyncio.Lock` serialisation. `pipeline.py` deliberately untouched — it is Agent 2's surface. 12 tests, pipeline mocked. |
| 5 | `Track D: offline demo-fixture export + committed apps/web/public JSON` | `apps/api/scripts/export_demo_fixture.py` dumps `demo_voyage_fixture()` with `model_dump_json(by_alias=True)`; committed `apps/web/public/demo-fixture.json` for offline-demo fallback. 3 tests guard the alias + round-trip. |
| 6 | `Track D: doc cleanups + offline smoke script` (this commit) | This file, the Rotterdam rewrite of `05-synthetic-data.md`, `branch-state.md`, `scripts/smoke_pipeline.sh`, `scripts/README.md`, README alignment. |

## What this PR did NOT touch

- `apps/api/portside_api/pipeline.py` — Agent 2's incoming-PR surface (plug
  Agent 3 / Agent 4 into the existing SEAM, then call `store.patch(voyage_id,
  stage=..., ...)` per the contract published in `storage.py`).
- `apps/api/portside_api/agents/**` — Agent 1's just-merged extractor/calculator;
  Agent 2's pending analyst/drafter. We did not retrofit Agent 1's prompts to
  use `load_prompt()`; that's a future surgical change, not this PR's scope.
- `apps/api/portside_api/prompts/{extractor,classifier}.md` — Agent 1's owned.
- `apps/web/lib/demo.ts`, `apps/web/lib/api.ts`, `apps/web/app/**`,
  `apps/web/components/**` — Agent 2's frontend live-wiring surface.
- `apps/api/tests/test_calculator.py` — Agent 1's gate.
- `synthetic-data/**` — Agent 1's owned.

## Staged-update contract published for Agent 2

The `VoyageStore.patch(voyage_id, **fields)` shape (see `apps/api/portside_api/storage.py`
docstring) lets Agent 2's `pipeline.py` extension emit per-stage updates so the
frontend's `pollVoyage` actually animates `extracting → calculating → analyzing
→ drafting → done`:

```python
await store.patch(voyage_id, stage="extracting")
extraction = await extractor.run(...)
await store.patch(voyage_id, stage="calculating", extraction=extraction)
laytime, dispute = await asyncio.gather(
    calculator.run(...), analyst.run(...),
)
await store.patch(voyage_id, stage="drafting", laytime=laytime, dispute=dispute)
packet = await drafter.run(...)
await store.patch(voyage_id, stage="done", packet=packet)
```

Optional — the existing call site (Wave II's `_run_pipeline_bg`) keeps working
unchanged: pipelines that don't emit per-stage updates still go `uploaded → done`.

## How to rebase Agent 2's branch

```bash
git fetch origin
git rebase origin/main      # once Track D is merged
# OR mid-flight:
git rebase agent-3/track-d-foundation
```

Then in `agents/analyst.py` and `agents/drafter.py`:

```python
from portside_api.prompts import load_prompt
SYSTEM = load_prompt("cross_cutting") + "\n\n" + load_prompt("analyst")
```

`agents/llm.py` already exists (Agent 1 merged it). For Agent 4's streaming,
extend `llm.py` with a `stream_text(...)` primitive when needed.

## Acceptance — the four pre-merge checks

1. **Runs locally**: `cd apps/api && uv sync && uv run uvicorn portside_api.main:app --port 8000`; `curl localhost:8000/healthz` → 200. POST returns instantly with a `voyage_id`. (Note: the pipeline behind it will call the real Anthropic API once env is set — gated behind user authorisation.)
2. **The math test passes**: `uv run pytest tests/test_calculator.py -v` — 3/3 green.
3. **Eyes on the diff**: self-merge, < 30-lines-per-file boundary touches, track-internal. The one boundary line is `main.py` (refactored to async-bg); the only cross-lane file we edit is `notes/05-synthetic-data.md` (doc-drift fix, no code).
4. **Agent-written code rule**: every chunk read line-by-line before commit; no hallucinated imports; no `print()` debug residue; lockfile untouched.

Total Track D: 33 passing tests, 0 network calls.

## Cut order if any of this is too much

- `notes/16-aws-deploy.md` + `Dockerfile` + `apprunner.yaml` + `amplify.yml` could be reverted; local demo doesn't need them.
- `scripts/smoke_pipeline.sh` could be dropped; Wave 2 manual integration smoke catches the same thing.
- `apps/web/public/demo-fixture.json` is nice-to-have; the live API is the primary path.

Do **NOT** cut: settings, prompts/cross_cutting.md, async-bg `main.py`, `store.patch()`. These are why Agent 2's PR can move faster.
