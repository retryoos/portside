# Pre-Deployment Checklist — everything to do before we ship

> Status at time of writing: Agents 1 (ingestion+calc), 2 (analyst/drafter + live
> frontend wiring + inline-revise), and 3 (Track D foundation/deploy artifacts)
> are all merged to `main`. Currency switched **USD → EUR** on branch
> `chore/eur-and-predeploy` (relabel, numbers unchanged — quantum stays
> **EUR 84,375.00**). This doc is the gate between "merged" and "deployed".

Single source of truth for the demo voyage: **MT Aegean Pioneer · Ras Tanura →
Rotterdam · EUR 84,375.00** (72 / 117 / 45h @ EUR 1,875/hr; contested 4h weather
on 17 May, CP cl. 14 precipitation > 0.5 mm/hr, *The Mexico 1* [1990]).

Work top-down. Don't deploy until §1–§3 are green.

---

## 1. Code-complete verification (run locally, all green)

- [ ] **Calculator gate** — `cd apps/api && uv run pytest tests/test_calculator.py -v` → asserts `demurrage_due_eur == 84375.0`. This is the headline number; do not ship if red.
- [ ] **Full backend test suite** — `uv run pytest -v` (test_calculator, test_storage, test_settings, test_prompts, test_main_async, test_reviser, test_export_demo_fixture). Confirm `pytest-asyncio` is installed for the async tests; `httpx` (needed by `TestClient`) comes transitively via the `anthropic` SDK.
- [ ] **Backend boots** — `uv sync && uv run uvicorn portside_api.main:app --port 8000`; `curl localhost:8000/healthz` → `200`.
- [ ] **Async POST is non-blocking** — `curl -F cp=@x.pdf -F nor=@y.pdf -F sof=@z.pdf -F perspective=owner localhost:8000/voyages` returns `201` with a `voyage_id` **instantly**; `GET /voyages/{id}` shows `stage` advancing `uploaded → extracting → … → done`.
- [ ] **Frontend typecheck + build** — `cd apps/web && npm install && npx tsc --noEmit && npm run build`. (The `_usd → _eur` rename touched `lib/types.ts` + every component reading those fields — tsc is the proof they all line up.)
- [ ] **Real end-to-end run** — generate the demo PDFs (`pip install -r synthetic-data/requirements.txt && python synthetic-data/generate.py`), upload them, watch all four agents, confirm: quantum **EUR 84,375.00**, dispute flags e6, letter cites *The Mexico 1* + the 0.5 mm/hr threshold, and **every figure shows EUR** (UI, letter, SoF table).
- [ ] **Offline smoke** — `bash apps/api/scripts/smoke_pipeline.sh` (asserts `demurrage_due_eur == 84375`).

## 2. Known gaps to close (carry-overs from the parallel merge)

- [x] **Cross-cutting prompt wired (done in this PR).** `extractor.py`, `calculator.py` (classifier), `analyst.py`, and `drafter.py` now prepend `load_prompt("cross_cutting")` to their system text, so the shared AI-tell-suppression + EUR/clause/event formatting rules apply to every agent.
- [x] **`client.py` confirmed unnecessary (reference removed).** It was never created and is referenced nowhere — every agent uses `agents/llm.py`. No action needed.
- [ ] **EUR copy sweep.** Skim the rendered letter, dispute narrative, and the three screens for any lingering "$" or "dollar" wording in free-text prose the token-rename didn't catch.

## 3. Secrets & configuration

- [ ] `ANTHROPIC_API_KEY` — present in `apps/api/.env` locally; set as an App Runner env var for deploy. **Never commit it** (`.env` is gitignored; verified the key is not in history).
- [ ] `ANTHROPIC_MODEL_PRIMARY=claude-sonnet-4-6` (default); `ANTHROPIC_MODEL_ESCAPE=claude-opus-4-7` available as the per-agent quality escape.
- [ ] `CORS_ORIGINS` — local default `http://localhost:3000`; on deploy set to the Amplify domain (comma-separated if both).
- [ ] `NEXT_PUBLIC_API_URL` — local default `http://localhost:8000`; on Amplify set to the App Runner URL.
- [ ] Rotate the Anthropic key if it was ever pasted outside `.env` (belt-and-suspenders; no git leak found).

## 4. Backend deploy — AWS App Runner (off the critical path; local demo is primary)

Per `notes/02-architecture.md §12` + `notes/16-aws-deploy.md`.
- [ ] `docker build -t portside-api apps/api` builds clean (base `python:3.12-slim`, no cairo/pango — PDF export is client-side). Run only if OrbStack/Docker is up.
- [ ] Push to ECR **or** use App Runner source-deploy with `apps/api/apprunner.yaml`.
- [ ] Set env vars on the service: `ANTHROPIC_API_KEY`, `CORS_ORIGINS` (= Amplify domain), `ANTHROPIC_MODEL_PRIMARY`.
- [ ] Hit the deployed `/healthz` → `200`. Note the service URL for `NEXT_PUBLIC_API_URL`.

## 5. Frontend deploy — AWS Amplify Hosting

- [ ] Connect the GitHub repo; app root `apps/web`; build spec `apps/web/amplify.yml` (Next 15 App Router).
- [ ] Set `NEXT_PUBLIC_API_URL` = the App Runner URL.
- [ ] Add the resulting Amplify domain to the backend's `CORS_ORIGINS` and redeploy the API.
- [ ] First-build gotchas budget ~30–45 min.

## 6. Post-deploy verification

- [ ] Open the Amplify URL → three screens render; "Try the demo voyage" shows **EUR 84,375.00** from the committed `apps/web/public/demo-fixture.json` (works even if the live API is cold).
- [ ] Live upload against the deployed API → staged polling animates → real packet in EUR.
- [ ] Browser console clean (no CORS errors, no 4xx/5xx on the happy path).

## 7. Demo-readiness (non-negotiable from 18:00)

Per `notes/08-demo-and-pitch.md` + `notes/09-pre-merge-protocol.md §3`.
- [ ] Two clean dress rehearsals of the 5-minute flow on the demo laptop, no code changes between.
- [ ] **Backup video** recorded (~18:00) in case live fails on stage.
- [ ] `apps/web/public/demo-fixture.json` confirmed as the offline fallback ("Try the demo voyage").
- [ ] Error-state UX checked: kill the API mid-run → `/claim` shows a clean inline error, not a blank screen.
- [ ] `/impeccable polish` + `npx @google/design.md lint apps/web/DESIGN.md` clean; numbers formatted `EUR 84,375.00`, timestamps `17 May 14:00 LT`.
- [ ] Demo laptop: full screen, 100% zoom, clean wallpaper/dock; phone-hotspot ready if venue wifi dies.
- [ ] **Entire**: run `entire dispatch` near the freeze and capture the link for the submission form (judging requirement).

## 8. Go / no-go & rollback

- **Ship-blockers:** calculator gate red · frontend won't build · live run doesn't reach `done` · quantum not EUR 84,375.
- **Cut order if behind** (mirror `notes/00-PLAN.md §12`): drop the AWS deploy (demo local-only) → drop Excel/extra Tier-1 → accept "good enough" prose. Never cut: the gate, the offline fixture, the backup video, the dispatch.
- **Rollback:** the demo is the local laptop; if AWS misbehaves, present locally — nothing on stage depends on the deploy.

## 9. Sanity passes (quick, before freeze)

- [ ] **Latency** < ~25s end-to-end on the demo doc (`notes/02-architecture.md §5`); confirm Agent 2∥3 don't serialize unnecessarily.
- [ ] **Prompt cache** working: `usage.cache_read_input_tokens > 0` on agents after the first call (the cached system/CP prefix).
- [ ] **Cost** per voyage ~EUR 0.05–0.10 with Sonnet 4.6.
- [ ] No debug `print()`/`console.log` spam on the happy path.
