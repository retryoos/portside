# Runbook — getting the app running on May 28th

> Practical, terminal-by-terminal. Print this or keep it open on the second laptop. If something breaks, the recipes at the end have a fix for it.

The shape of the day: three engineers, each with two terminals open (one for `claude`, one for the dev server). One designated **demo laptop** that owns the working build at 19:00.

---

## 1. Pre-hackathon checklist (May 27 evening)

Every engineer's laptop must pass this before going to sleep on May 27.

### Device split for our two machines

| Machine        | Owner         | Role        | Container/Linux tooling                                              |
| -------------- | ------------- | ----------- | -------------------------------------------------------------------- |
| macOS          | you           | **Backend** (`apps/api`) | **OrbStack** (optional — only to test the App Runner Docker image). Day-to-day dev is just `uv run uvicorn`, no container. |
| Windows        | your friend   | **Frontend** (`apps/web`) | **Nothing** — native Windows + Node + pnpm. No WSL, no Docker, no OrbStack needed for frontend. |

**Why no WSL/containers are required anymore:** the backend has **zero native dependencies** now (FastAPI + uv + `pdfplumber` + anthropic SDK are all pure Python — PDF export moved to the browser, so weasyprint/cairo/pango are gone from the runtime). The backend runs natively on macOS *and* native Windows.

- **OrbStack (macOS only):** it does **not** exist on Windows. On your Mac it's optional — use it *only* to test the App Runner deploy container (`docker build` + `docker run` the backend image) before pushing. You do not need it to develop.
- **If the Windows box ever has to run the backend:** since there are no native deps, native Windows + `uv` works. WSL2 is still nice for toolchain parity (and is where you'd run Docker, since OrbStack is Mac-only) — but it is no longer required. `wsl --install` in an admin PowerShell if you want it.

### What each agent must check is installed

**Backend agent (macOS) — check before starting:**
```bash
python3 --version     # expect 3.12+
uv --version          # expect >= 0.5   (install: curl -LsSf https://astral.sh/uv/install.sh | sh)
git --version
claude --version      # Claude Code CLI
entire --version      # Entire CLI — REQUIRED (see §1c). install: curl -fsSL https://entire.io/install.sh | sh
entire status         # must show Entire ENABLED for this repo before you write any code
jq --version          # nice to have for poking JSON   (brew install jq)
# OrbStack only if you want to test the deploy container — not required for dev
cat apps/api/.env     # confirm ANTHROPIC_API_KEY is set (see Environment below)
```

**Frontend agent (Windows) — check before starting:**
```powershell
node --version        # expect v22.x   (install Node 22 LTS)
pnpm --version        # expect >= 9     (install: corepack enable)
git --version         # Git for Windows
claude --version      # Claude Code CLI
entire --version      # Entire CLI — REQUIRED (see §1c)
entire status         # must show Entire ENABLED for this repo before you write any code
# No Python, no WSL, no Docker needed for frontend
```

### Full software prerequisites (reference)

```bash
# Python 3.12+ via uv  (backend machine only)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version              # expect >= 0.5

# Node 22+ via fnm or nvm  (both machines; Windows can use the Node MSI installer)
fnm install 22 && fnm use 22
node --version            # expect v22.x

# pnpm
corepack enable
pnpm --version            # expect >= 9

# gh CLI
gh --version              # expect >= 2.40
gh auth status            # confirm logged in as retryoos

# Claude Code
claude --version          # expect latest
```

### Repo bootstrap

```bash
cd ~/Desktop/Code/FlorentHackathon/Source
git pull
ls notes/                 # confirm the planning docs are present

# Entire — install + enable BEFORE writing any code (see §1c)
curl -fsSL https://entire.io/install.sh | sh
entire enable             # installs git hooks in THIS clone — each machine runs this
entire status             # confirm ENABLED
```

**Each machine must run `entire enable` in its own clone** — the git hooks that capture sessions are local to each clone. The captured session data is committed to the repo and shared.

### Environment

Create `apps/api/.env` (do NOT commit):
```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL_PRIMARY=claude-sonnet-4-6
ANTHROPIC_MODEL_ESCAPE=claude-opus-4-7   # per-agent escape hatch only — flipped in code for a specific agent if writing quality fails at the 16:00 polish round
```

Create `apps/web/.env.local` (do NOT commit):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Test the API key

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":50,"messages":[{"role":"user","content":"say hi"}]}'
```

---

## 1c. Entire — session capture + dispatch (JUDGING REQUIREMENT)

> The judges said: *"Submit with Entire and use it to give an overview of what you did (dispatches) so we can win the prizes."* This is tied to the prize. Treat it as mandatory, not optional.

**What Entire is:** a git-observability CLI ([entireio/cli](https://github.com/entireio/cli), [docs](https://docs.entire.io/cli/commands)) that captures your AI agent (Claude Code) sessions and indexes them alongside your commits — a searchable record of *how* the code was written. `entire dispatch` then generates the overview the judges want.

**The hard timing rule:** Entire only captures sessions that happen **after** `entire enable`. If you enable it late, all earlier agent work is invisible to the dispatch. **So `entire enable` is the first thing on every machine, before any coding.** Each agent's pre-flight (§1) checks `entire status` returns ENABLED.

**Workflow:**
```bash
# Once per machine, at setup (already in Repo bootstrap above):
curl -fsSL https://entire.io/install.sh | sh
entire enable
entire status                 # ENABLED

# During the day — sanity check it's tracking:
entire session info           # shows agent, model, tokens, files touched, checkpoint linkage

# At submission (~18:30, see §submission):
entire auth login             # if using cloud dispatch (shareable link for judges)
entire dispatch               # generates the overview of everything the agents built
#   or, no-account fallback:
entire dispatch --local       # generates from local repo data using your local agent CLI
```

**For the submission:** run `entire dispatch` near the freeze, capture the dispatch link/output, and include it in whatever the hackathon submission form asks for. This is the "overview of what you did" the judges scored on.

---

## 1b. Two-agent parallel kickoff (backend + frontend → two PRs)

Two Claude Code sessions work the same repo at the same time with **zero conflict**, because backend (`apps/api/`) and frontend (`apps/web/`) are different directories. Each agent works on its own branch and opens its own PR.

### The contract between them
The only shared thing is **[04-schemas.md](04-schemas.md)** (the `VoyageState` shape) and the **mock `GET /voyages/{id}` endpoint**. The backend agent ships these *first* so the frontend agent has something real to render against.

### The handoff sequence
```
Backend agent  ──PR #1 (schemas + mock endpoint)──►  main
                                                       │
Frontend agent ──pulls main, wires API client─────────┘
       │
       └── both continue in parallel on their own branches / PRs
```
The frontend agent does **not** have to wait to *start* — it scaffolds Next.js and renders against the example `VoyageState` JSON copied from [04-schemas.md §8](04-schemas.md) as a local fixture, then swaps to the live endpoint once PR #1 lands on `main`.

### Branches
- Backend: `track-a/api-skeleton`, then `track-a/agent1-extractor`, etc.
- Frontend: `track-c/web-skeleton`, then `track-c/laytime-table`, etc.

Follow the merge rules in [09-pre-merge-protocol.md](09-pre-merge-protocol.md).

---

### Kickoff brief — BACKEND agent (macOS, you)

Paste this into your `claude` session:

> You are building the backend for Portside (`apps/api/`). **First run `entire status` and confirm it shows ENABLED — if not, run `entire enable` before writing any code (judging requirement, see §1c).** Then read `notes/02-architecture.md`, `notes/03-agents.md`, and `notes/04-schemas.md`.
>
> **PR #1 — `track-a/api-skeleton` (do this first and push to main so the frontend agent can start):**
> 1. Scaffold `apps/api` with `uv` (Python 3.12, FastAPI, uvicorn, pydantic v2, anthropic, pdfplumber).
> 2. Create `portside_api/schemas.py` with the Pydantic models exactly as defined in `notes/04-schemas.md` (`VoyageState`, `ExtractionResult`, `LaytimeResult`, `DisputeAnalysis`, `ClaimPacket`, etc.).
> 3. Create `portside_api/main.py`: `POST /voyages` (multipart cp/nor/sof/perspective → returns `{voyage_id}`), `GET /voyages/{id}` (returns a hard-coded mock `VoyageState` matching the worked example in 04-schemas.md §8), and `GET /healthz`. Enable CORS for `http://localhost:3000`.
> 4. Confirm `uv run uvicorn portside_api.main:app --reload --port 8000` serves and `curl localhost:8000/voyages/test` returns the mock. Open PR, merge to main.
>
> **PR #2+ (your own branches, after #1 is on main):** implement the real pipeline — `pdfplumber` text extraction helper, then Agent 1 (extractor), Agent 2a (classifier) + 2b (deterministic Python calculator with a `tests/test_calculator.py`), Agent 3 (dispute analyst), Agent 4 (drafter). The orchestrator runs Agent 2 + Agent 3 in parallel via `asyncio.gather`. Use `claude-sonnet-4-6` for all agents. No server-side PDF — the letter content goes into `ClaimPacket` and the frontend renders/exports it.
>
> Check in with me after PR #1 is pushed.

### Kickoff brief — FRONTEND agent (Windows, your friend)

Paste this into the `claude` session on the Windows machine:

> You are building the frontend for Portside (`apps/web/`). **First run `entire status` and confirm it shows ENABLED — if not, run `entire enable` before writing any code (judging requirement, see §1c).** Then read `notes/06-frontend.md` (especially §0 — the mandatory `/impeccable` + `apps/web/DESIGN.md` workflow), `apps/web/DESIGN.md`, and `notes/04-schemas.md`.
>
> **PR — `track-c/web-skeleton`:**
> 1. Scaffold `apps/web` with Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui. Load the fonts and tokens from `apps/web/DESIGN.md` (Fraunces / IBM Plex Sans / JetBrains Mono).
> 2. Build the three-panel layout (Documents | Laytime Timeline | Claim Packet) per `notes/06-frontend.md`, rendering against a **local fixture** — copy the example `VoyageState` JSON from `notes/04-schemas.md §8` into `apps/web/lib/fixture.ts`. This lets you build the whole UI without waiting for the backend.
> 3. Create `apps/web/lib/types.ts` (zod schemas mirroring the Pydantic models) and `apps/web/lib/api.ts` (typed fetch client pointed at `NEXT_PUBLIC_API_URL`).
> 4. Run `/impeccable shape` before building each surface and `/impeccable audit` after. Run `npx @google/design.md lint apps/web/DESIGN.md`.
> 5. Once the backend's PR #1 is on `main` (it exposes `GET /voyages/{id}`), `git pull`, then swap the local fixture for a live `react-query` poll of the endpoint.
>
> The claim-letter PDF export is **client-side** (`html2pdf.js`) — there is no backend PDF endpoint.
>
> Check in with me when the three panels render against the fixture.

If you don't get back a 200 with a response, fix it tonight. Not tomorrow.

### Confirm the Claude account you'll use tomorrow works

Open `claude` in the repo, give it a tiny task ("read notes/00-PLAN.md and summarise it in 3 lines"), confirm it responds. Note which account is currently active (`gh auth status` for the GitHub side; Claude account is shown at session start).

---

## 2. Morning of (08:00–09:45)

### 08:00 — arrive
Sit together. Power outlets. Confirm Wi-Fi. Open `Activity Monitor` to confirm nothing weird is hogging CPU.

### 08:30 — fleet assignment
Open `notes/fleet-assignments.md` (create it now) and write down, by name:
- Engineer A (track) → Claude account
- Engineer B (track) → Claude account
- Engineer C (track) → Claude account
- B1 (data factory) → Claude account
- B2 (prompt iter) → Claude account
- X1 (Gemini judge) → Glacdimitris (browser)

Commit this file. It's not a doc, it's a state record.

### 09:00 — CEO talks
Listen. Take notes if anything specific to maritime / Greek venture climate comes up; we'll reference it in the pitch.

### 09:30 — last setup
Each engineer:
- Two terminals open in `apps/api` and `apps/web`
- One terminal open as the `claude` session
- (If background workstream owner) one extra terminal as the background `claude` session

### 09:45 — go
Read the first row of [07-day-plan.md](07-day-plan.md). Then code.

---

## 3. Starting the app

### Terminal 1 — API
```bash
cd apps/api
uv sync                   # first time only
uv run uvicorn portside_api.main:app --reload --port 8000
# Should print: INFO: Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2 — Frontend
```bash
cd apps/web
pnpm install              # first time only
pnpm dev
# Should print: ready - started server on 0.0.0.0:3000
```

### Smoke test (in a third terminal)
```bash
curl http://localhost:8000/healthz
# expect: {"status":"ok"}

open http://localhost:3000
# expect: three-panel UI with empty dropzone
```

If both succeed, you're ready to develop.

---

## 4. Common operations

### Run the calculator unit test (THE test that must always pass)
```bash
cd apps/api
uv run pytest tests/test_calculator.py -v
```

### Generate synthetic data
```bash
cd synthetic-data
uv run python generate.py athens-weather-dispute
ls scenarios/athens-weather-dispute/
# expect: cp.pdf nor.pdf sof.pdf weather_record.pdf expected.json
```

### Run a full pipeline manually against a scenario
```bash
cd apps/api
curl -X POST http://localhost:8000/voyages \
  -F "cp=@../../synthetic-data/scenarios/athens-weather-dispute/cp.pdf" \
  -F "nor=@../../synthetic-data/scenarios/athens-weather-dispute/nor.pdf" \
  -F "sof=@../../synthetic-data/scenarios/athens-weather-dispute/sof.pdf" \
  -F "perspective=owner"
# expect: 201 {"voyage_id": "v_..."}

# Then poll:
curl http://localhost:8000/voyages/v_abc123 | jq .stage
# repeat every 1-2s until "done"
```

### Download the letter
```bash
# The letter PDF is generated client-side in the browser (Download PDF button),
# not by the backend — there is no /letter.pdf endpoint to curl. To verify the
# letter content exists, check the packet in the VoyageState:
curl http://localhost:8000/voyages/v_abc123 | jq '.packet.letter_segments'
```

### Reset state (kill the in-memory store)
```bash
# Just restart uvicorn. The dict is reset on process restart.
```

### Look at what an agent saw
The pipeline logs each Anthropic call to stdout with the prompt and the response. Watch the uvicorn terminal during a run. If you can't tell what went wrong from logs alone, add `print(...)` statements in `apps/api/portside_api/agents/{name}.py` and reload.

---

## 5. Recipes for things that break

### "uvicorn won't start — port 8000 in use"
```bash
lsof -ti :8000 | xargs kill -9
```

### "pnpm dev fails on a TypeScript error"
- Look at the error. Probably a missing import or a schema mismatch.
- Run `pnpm tsc --noEmit` to see all type errors at once.
- If the error is in `lib/types.ts`, sync with the Pydantic schemas in `apps/api/portside_api/schemas.py`.

### "Anthropic returns 529 (overloaded) / 429 (rate limit)"
- 529: retry once with 2s backoff. If it persists, switch the model to Sonnet 4.6 in the affected agent's call.
- 429: this account hit its limit. Switch the account on this terminal's `claude` session AND on the Anthropic API key if it's a per-account key. Use a reserve account from the fleet (see [10-ai-fleet-playbook.md](10-ai-fleet-playbook.md)).

### "Agent 1 extraction returns null for fields that are clearly in the PDF"
- Check that the PDF is actually being sent as a `document` content block, not converted to base64 text.
- Confirm the Anthropic SDK version supports PDF input (>= the version that introduced native PDF support; we use the latest).
- If a specific field is consistently null, the prompt may need a more explicit instruction. Edit `apps/api/portside_api/prompts/extractor.md` and reload.

### "The laytime arithmetic doesn't match the expected number"
This is the most important class of bug. Procedure:
1. Pause. This is the demo's headline figure.
2. Run `uv run pytest tests/test_calculator.py -v` to confirm the test catches it.
3. If the test doesn't catch it, add a test case for the failing scenario first.
4. Walk through `calculator.py` with `print(...)` statements showing each event's duration and the running total.
5. The bug is almost always: wrong timezone handling, off-by-one on the demurrage threshold, or wrong rounding.

### "The claim-letter PDF download is broken"
PDF export is **client-side** (`html2pdf.js` on the rendered letter HTML) — there is no weasyprint, no backend PDF endpoint, no cairo/pango to install. If the download fails:
- Check the letter actually rendered in the right panel first (the PDF is generated from that DOM node).
- Confirm the Fraunces / IBM Plex / JetBrains Mono fonts are loaded before export, or the PDF falls back to default fonts.
- Worst case fallback: `window.print()` with the print stylesheet → "Save as PDF" in the browser dialog. Zero dependencies.

### "weasyprint won't install (only matters for generating synthetic INPUT PDFs)"
weasyprint is used **only** by the synthetic-data background workstream to generate the demo CP/NOR/SoF PDFs — it never ships in the product. Run it on macOS (`brew install cairo pango gdk-pixbuf libffi`) or inside WSL2 Ubuntu (`sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0`). If it's fighting you, generate the synthetic PDFs by opening the HTML templates in a browser and printing to PDF instead.

### "The Next.js dev server is slow / hot reload broken"
```bash
rm -rf apps/web/.next
pnpm dev
```

### "I'm offline / Wi-Fi is dropping"
- Phone hotspot — tether to the iPhone of whichever engineer has the best signal.
- Anthropic calls require internet. Without internet, the pipeline can't run.
- The frontend works offline against cached data, but no new voyages can be processed.

### "The demo laptop is acting weird and the demo is in 10 minutes"
- Reboot it.
- Have the backup video ready (recorded at 17:30 per the day plan).
- Have the fallback `VoyageState` JSON ready in the frontend's `public/` folder; you can wire it as a "demo mode" via a query param `?demo=true`.

---

## 6. Snapshots and backups

At each integration checkpoint (11:15, 13:00, 15:00, 17:30), the demo-laptop owner does:

```bash
git add -A
git commit -m "checkpoint $(date +%H:%M)"
git push
```

If the laptop fails between checkpoints, the most you lose is 75 minutes of work.

Additionally at 17:30:
```bash
# Capture a known-good run as a fixture
curl -X POST http://localhost:8000/voyages -F ...
# Wait until stage=done, then:
curl http://localhost:8000/voyages/{id} > apps/web/public/demo-fixture.json
```

This file becomes the "if everything else fails, the frontend renders this" disaster fallback.

---

## 7. Demo laptop hygiene

The laptop that does the live demo at 19:00:

- [ ] Closed all tabs except `http://localhost:3000` and the backup video in another tab
- [ ] Notifications silenced (Do Not Disturb)
- [ ] Slack quit, Discord quit, email quit
- [ ] Wallpaper plain — no personal photos
- [ ] Dock cleared
- [ ] Browser zoom at 100%
- [ ] Battery > 80% or plugged in
- [ ] HDMI / USB-C adapter for the projector ready
- [ ] One USB drive plugged in containing: the three demo PDFs, the backup video, the fallback JSON, the printed claim letter

---

## 8. Account / credential locations on macOS

Useful to know if you have to switch accounts mid-day:

| Tool             | Location                                              |
| ---------------- | ----------------------------------------------------- |
| `gh` auth        | `~/.config/gh/hosts.yml`                              |
| `git` credentials| macOS Keychain (for HTTPS) or `~/.ssh/` (for SSH)     |
| Claude Code      | `~/.claude/` (project state) — account from sign-in flow |
| Anthropic API    | `.env` files in each repo, sourced from process env   |

To switch a `gh` account: `gh auth switch`. To switch a Claude Code account: sign out, sign in (`/login` inside the REPL).

---

## 9. Quick command reference

```bash
# Most-used during the day:
uv run uvicorn portside_api.main:app --reload --port 8000
pnpm dev
uv run pytest tests/test_calculator.py -v
claude

# In a Claude Code session, useful slash-commands:
/clear        # reset conversation context (start fresh)
/login        # change Claude account
/help         # see all commands
```

---

## 10. End-of-day shutdown (~21:00)

After the awards:

```bash
git add -A
git commit -m "end of hackathon: final state"
git push
```

Pin the demo video and the printed claim letter in the team's shared drive. We use them in the contest pitch on the following days.

Then go sleep. We start Phase C on May 29 — see [extended_plan.md](extended_plan.md#10-phase-c--taking-portside-to-the-startup-contest-the-week-after).
