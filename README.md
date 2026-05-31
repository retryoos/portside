# Papership.Ai

**Maritime Demurrage and Laytime Resolution Agent.** Built at the Florent x Panathēnea Hackathon, Athens, 28 May 2026.

> Three voyage PDFs in. One legally structured, EUR denominated demurrage claim packet out, in under a minute.

---

## The problem

When a vessel finishes a port call and laytime is disputed, a claims team spends two to four days pulling together the Charter Party, the Notice of Readiness, and the Statement of Facts, working out by hand which hours count against laytime and which are excepted, arguing over weather stoppages, and drafting a claim letter that may or may not recover what is owed. A single tanker sitting idle runs tens of thousands of euros per day, and industry demurrage exposure runs into the billions annually. The closest existing tools are Excel templates and specialist advisors. Neither is software.

This is revenue recovery and legal defense, the highest value workflow an agent can take on.

## What Papership.Ai does

Upload three documents (Charter Party excerpt, Notice of Readiness, Statement of Facts) and choose the owner or charterer perspective. Papership.Ai runs a four step agent pipeline and returns:

- a per event **laytime calculation table** with a running total and the demurrage crossover,
- the **contested events** flagged with a plain English argument and a strength rating,
- the **claim quantum** in EUR,
- a formal **BIMCO style claim letter**, exportable to PDF in the browser,
- a **time bar** date so the claim is not lost to the 90 day deadline.

### The demo voyage

MT Aegean Pioneer, Ras Tanura to Rotterdam, CP dated 12 February 2026.

| Figure | Value |
| --- | --- |
| Laytime allowed | 72 h (SHINC) |
| Laytime used | 117 h |
| On demurrage | 45 h |
| Demurrage rate | EUR 45,000 / day (EUR 1,875 / h) |
| **Demurrage due** | **EUR 84,375.00** |
| Contested | 4 h weather stoppage on 17 May, CP clause 14 (precipitation > 0.5 mm/hr not met) |

This run is real: feeding the three demo PDFs through the live pipeline produces `stage=done` and `demurrage_due_eur = 84,375.00`.

## Why it is defensible

These are the points a shipping professional will check, and what Papership.Ai does about each:

1. **The arithmetic is deterministic Python, not an LLM.** The model classifies each Statement of Facts event (does this time count, which exception applies); a plain Python function then walks the timeline, sums the hours, splits the row where the allowance is exhausted, and multiplies by the rate. The number on screen is reproducible and auditable. A test (`tests/test_calculator.py`) locks it to EUR 84,375.00.
2. **Every line cites its basis.** Laytime rows reference the clause; dispute findings reference the CP clause number and the SoF event id. Output reads like a junior maritime associate wrote it.
3. **It scales to real, long documents.** Real Statements of Facts are long event logs. Papership.Ai distills the long text into a compact structured timeline once (Agent 1), then the downstream agents reason over that small object instead of re-reading raw text. This is why the split into specialized agents is a feature, not over engineering.
4. **Confidence is a word, not a gimmick.** Owner position strength shows as Strong, Arguable, or Weak, never a fake percentage.
5. **Time bar awareness.** The 90 day contractual deadline is surfaced on every claim. Missing it forfeits the claim, the single biggest avoidable mistake in the industry.

## How it works

```
                three PDFs + perspective
                          |
                  pdfplumber (local text + table extraction)
                          |
      Agent 1  Extractor        Sonnet 4.6, strict structured output  -> ExtractionResult
                          |
      Agent 2  Calculator        2a classify events (LLM)  ->  2b sum hours (deterministic Python)  -> LaytimeResult
                          |
      Agent 3  Dispute Analyst   Sonnet 4.6  -> DisputeAnalysis (citations, strength, incremental EUR)
                          |
      Agent 4  Claims Drafter    Sonnet 4.6  -> ClaimPacket (BIMCO letter + narrative)
                          |
                  VoyageState (polled by the UI, stage by stage)
```

- **Async, staged.** `POST /voyages` returns a `voyage_id` immediately and runs the pipeline in the background, writing each stage (`extracting`, `calculating`, `analyzing`, `drafting`, `done`) to the store so the UI animates live progress.
- **One model, four agents.** Claude Sonnet 4.6 by default for cost and latency; Claude Opus 4.7 is a per agent quality escape via `ANTHROPIC_MODEL_PRIMARY`. Every agent shares a cross cutting prompt prefix (`prompts/cross_cutting.md`) that suppresses AI tells and enforces EUR, clause by number, and event by id formatting.
- **Prompt caching** on the charter party text across agent calls keeps per voyage cost around EUR 0.05 to 0.10.
- **Graceful fallback.** If a PDF cannot be parsed, the pipeline serves the canonical demo voyage rather than failing the demo.

## Product surfaces

| Route | What it is |
| --- | --- |
| `/` | Redirects to the dashboard |
| `/cases` | Dashboard: every voyage, newest first, each row clickable. "New voyage claim" reveals the dropzone and "Try the demo voyage" |
| `/cases/<id>` | Case detail: the formal letter, the laytime table, Sources / Calculation / Documents tabs, client side PDF export |
| `/vessels`, `/vessels/<name>` | Fleet view: voyages grouped by vessel with aggregate quantum and last activity |
| inline revise | Highlight a sentence in the letter and ask for a rewrite; the server rejects any rewrite that changes a monetary value or drops a clause or event reference |
| "Try the demo voyage" | Renders a committed offline fixture with no backend call, so the demo works even if the API is cold |

## Tech stack

- **Backend:** FastAPI, async Python 3.12, Pydantic v2 (the frozen `VoyageState` contract), the Anthropic SDK with strict structured output, `pdfplumber` for local PDF text extraction. In memory store keyed by `voyage_id` (no database for the demo).
- **Frontend:** Next.js 15 (App Router), Tailwind v4 with a design token theme, Fraunces / IBM Plex Sans / JetBrains Mono, client side PDF export via `html2pdf.js`.
- **PDF export is client side**, so there are no native dependencies (no cairo or pango) anywhere; the backend image is clean `python:3.12-slim`.

## API surface

```
GET  /healthz                     liveness
GET  /voyages                     list voyages (dashboard rows: VoyageSummary)
GET  /vessels                     voyages grouped by vessel (VesselSummary)
POST /voyages                     multipart cp, nor, sof + perspective -> { voyage_id } (runs pipeline in background)
GET  /voyages/{id}                current VoyageState (poll every ~500 ms)
POST /voyages/{id}/revise         inline revision with server side safety gate
```

## Run it locally

Prerequisites: `uv` (Python), Node.js, and `ANTHROPIC_API_KEY` in `apps/api/.env` (a repo root `.env` also works).

```
# Terminal 1: backend (reload scoped to source, not .venv)
cd apps/api
uv sync
./dev.sh                      # serves http://localhost:8000

# Terminal 2: frontend
cd apps/web
npm install
npm run dev                   # serves http://localhost:3000 (or 3001)
```

Open the dashboard at `http://localhost:3000/cases`, then either click **Try the demo voyage**, or click **New voyage claim**, choose **Owner**, and drop the three PDFs from `synthetic-data/scenarios/rotterdam-weather-dispute/`. Watch the four agents step through to a EUR 84,375.00 claim.

Backend only smoke test:

```
D=synthetic-data/scenarios/rotterdam-weather-dispute
VID=$(curl -s -F cp=@$D/cp.pdf -F nor=@$D/nor.pdf -F sof=@$D/sof.pdf -F perspective=owner localhost:8000/voyages | python3 -c "import sys,json;print(json.load(sys.stdin)['voyage_id'])")
sleep 35
curl -s localhost:8000/voyages/$VID | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['stage'], d['laytime']['demurrage_due_eur'])"
# -> done 84375.0
```

The three demo PDFs are committed; regenerate them anytime with `cd apps/api && uv run --with fpdf2 python ../../synthetic-data/generate.py`.

## Repository layout

```
apps/
  api/                         FastAPI backend
    portside_api/
      main.py                  routes (async background pipeline)
      pipeline.py              orchestrator
      pdf.py                   pdfplumber extraction
      agents/                  extractor, calculator (classify + arithmetic), analyst, drafter
      prompts/                 role prompts + cross_cutting prefix + load_prompt()
      schemas.py               frozen Pydantic contract
      storage.py               in memory store
      fixtures.py              the canonical demo voyage (single source of truth)
      reviser.py               inline revision + safety gate
    tests/                     calculator gate, storage, settings, prompts, async API, reviser
    Dockerfile, apprunner.yaml AWS App Runner deploy artifacts
  web/                         Next.js 15 frontend (dashboard, case detail, vessels, claim, revise)
    DESIGN.md                  design tokens contract
    lib/demo.ts                offline demo fixture (mirrors fixtures.py)
synthetic-data/                demo PDF generator + committed scenario PDFs
notes/                         SYSTEM.md (built) · ROADMAP.md (planned) · OPERATIONS.md (run + deploy)
```

## Deployment

Artifacts are in the repo and kept off the critical path; the local laptop is the primary demo.

- **Backend:** `apps/api/Dockerfile` + `apprunner.yaml` for AWS App Runner. Set `ANTHROPIC_API_KEY` and `CORS_ORIGINS`.
- **Frontend:** `apps/web/amplify.yml` for AWS Amplify Hosting. Set `NEXT_PUBLIC_API_URL` to the App Runner URL.
- Full run, demo-deploy, and AWS-migration steps: [notes/OPERATIONS.md](notes/OPERATIONS.md).

## Scope and roadmap

In scope today: one voyage charter, one port call, one disputed laytime calculation, one claim packet, owner or charterer perspective, a multi case dashboard and a fleet view, inline letter revision, and client side PDF export.

Out of scope for the demo: multi port voyages, time charters, bunker and cargo damage and General Average, AIS integrations, user accounts, and persistence beyond the running process. Roadmap: SaaS seats for owners, charterers, and maritime lawyers; an AI native claims service on a recovery success fee; adjacent document heavy workflows (cargo damage, freight disputes, P and I correspondence); and inbox to outbox automation that assembles the voyage bundle from email and sends the approved letter.

## How it was built

Papership.Ai was built by a fleet of Claude agents working in parallel on isolated branches that merged into one trunk: an ingestion and calculation track (Agent 1), a reasoning, drafting, and live frontend track (Agent 2), a foundation, async plumbing, and deploy track (Agent 3), and a vessels track. Agent sessions were captured with the Entire CLI for the judging dispatch.
