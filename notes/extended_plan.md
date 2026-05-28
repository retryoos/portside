# Extended Plan — MVP + Stretch + Post-Hackathon Architecture

> Companion to [00-PLAN.md](00-PLAN.md). The other notes describe **what** we build. This describes **how** we build it, **in what order**, and **what we build next** once the MVP lands.

The principle behind every decision below: **the hackathon stack is the v0.1 stack, with persistence, auth, and deploy stubbed.** No throwaway code. When we win on May 28th, we spend the following week flipping switches, not rewriting.

---

## 1. The two-phase strategy

### Phase A — MVP (12 hours, May 28th)
Single demo path. One voyage. One scenario. No accounts. No persistence. Local laptop only. The full agent pipeline working end-to-end against the Piraeus weather dispute, rendered in the three-panel UI, exporting a BIMCO PDF.

This is what gets demoed at 19:00 and what gets the trophy.

### Phase B — Stretch tiers (the same day, if we finish early)
A prioritized list of needle-movers, each independent, each landable in 30–90 minutes once the MVP is in. We pick from the top, only as far down as time allows. See section 9.

### Phase C — Post-hackathon v0.1 (the week after)
Switch on persistence, auth, custom domain. Take to the Florent startup contest with: a working URL, signup with Supabase, three to five real-feeling seeded voyages in the database, the team's claim emails routed through SES. See section 10. (The Amplify + App Runner deploy itself is already done on hackathon day — Phase C adds the data and auth layers on top.)

---

## 2. Architectural spine (same for all three phases)

```
Browser (desktop primary, mobile-responsive)
   │
   ▼  HTTPS + JSON
FastAPI app (Python 3.12, async)
   │
   ├──► Anthropic API (Claude Sonnet 4.6 primary; Opus 4.7 per-agent escape hatch)
   ├──► Persistence layer (Phase A: in-memory · Phase B: SQLite file · Phase C: Supabase Postgres)
   ├──► Object storage (Phase A: /tmp · Phase C: Supabase Storage)
   └──► Auth (Phase A: none · Phase C: Supabase JWT verification)
```

Three things never change between phases:
1. **Schemas** ([04-schemas.md](04-schemas.md)). Pydantic models on the backend, mirrored TS types on the frontend.
2. **The four-agent pipeline.** Same orchestrator, same prompts, same models.
3. **The HTTP API surface.** `POST /voyages`, `GET /voyages/{id}` (letter PDF is generated client-side from the returned letter HTML — no backend export endpoint).

What changes is the **adapters** behind the routes (storage, persistence, auth) — wrapped behind interfaces so the swap is one-line.

```python
# apps/api/portside_api/storage.py
class VoyageStore(Protocol):
    async def save(self, state: VoyageState) -> None: ...
    async def load(self, voyage_id: str) -> VoyageState: ...

class InMemoryStore(VoyageStore): ...   # Phase A
class SQLiteStore(VoyageStore): ...     # Phase B
class PostgresStore(VoyageStore): ...   # Phase C
```

The pipeline never knows which store it's talking to.

---

## 3. Stack: hackathon vs. post-hackathon

| Layer            | Phase A (May 28)                       | Phase C (post-hackathon)                            |
| ---------------- | -------------------------------------- | --------------------------------------------------- |
| Frontend         | Next.js 15 + Tailwind + shadcn/ui      | **Same.** Deploy to **AWS Amplify Hosting** (sponsor-aligned; SSR-capable).        |
| Backend          | FastAPI + uvicorn (Python 3.12)        | **Same.** Deploy to **AWS App Runner** (container, scales to zero).                 |
| LLM              | Anthropic SDK · **Sonnet 4.6** for every agent | **Same.** Opus 4.7 is a per-agent escape hatch only. Add Bedrock fallback if margin matters at scale.|
| State            | In-memory dict keyed by `voyage_id`    | **Supabase Postgres** via SQLAlchemy + Alembic      |
| Files            | Local `/tmp` for PDFs                  | **Supabase Storage** (or S3 if we stay AWS-native)  |
| Auth             | None                                   | **Supabase Auth** (Next.js SDK + FastAPI JWT verification) |
| Polling          | `setInterval` + fetch                  | **Same.** Maybe SSE later.                          |
| PDF letter       | **Client-side** `html2pdf.js` on the rendered letter HTML | **Same.** No server-side PDF lib; no cairo/pango anywhere. |
| Word letter      | Optional, client-side `docx` (JS)      | **Same.** Cuttable.                                 |
| PDF parsing      | **`pdfplumber`** (MIT) for text + tables locally; Claude native PDF input only as fallback for scanned docs | **Same.** For scale-up consider `marker` / `docling` / `olmocr` (all OSS) for higher-quality extraction on noisy real-customer PDFs. |
| Email send       | Not built                              | SES (we have AWS credits)                           |
| Observability    | `print()` to stdout                    | Sentry (free tier) + CloudWatch                     |
| CI/CD            | None                                   | GitHub Actions: deploy on push to `main`            |
| Domain           | `localhost`                            | `portside.app` (~$15/yr) or similar — buy on May 29 |

**Anti-decisions** (things we are explicitly not picking):
- No tRPC, no GraphQL — REST + Pydantic + zod is simpler and matches our timeline.
- No Server Actions / Server Components data fetching for the polling flow — `react-query` is cleaner.
- No Turborepo — `pnpm` workspaces + `uv` are enough.
- No Docker for local hackathon dev — adds a layer of "why doesn't this work" pain. A minimal Dockerfile exists only for the App Runner backend deploy (and it's a clean `python:3.12-slim` now that PDF is client-side — no cairo/pango layers).
- No Redis, no SQS, no Lambda for v0.1 — pipeline is request-response and fits in one App Runner process.
- No Drizzle / Prisma — backend is Python, ORM is SQLAlchemy.
- No server-side PDF rendering — `html2pdf.js` in the browser. This is what lets the backend image stay dependency-light and the Windows dev box avoid the cairo/pango install entirely.

---

## 4. The skeleton build order (first 90 minutes)

The expensive thing isn't writing code, it's debugging integration. The order below maximizes the number of clock-minutes during which all three engineers can work on something real without waiting on each other.

| Minute | Engineer A (API)                                       | Engineer B (Agents + data)                             | Engineer C (Frontend)                                            |
| ------ | ------------------------------------------------------ | ------------------------------------------------------ | ---------------------------------------------------------------- |
| 0–10   | `uv init`, FastAPI hello-world, CORS enabled           | `synthetic-data/` dir, scenario folder structure        | `pnpm create next-app`, Tailwind + shadcn install                |
| 10–30  | Copy schemas from [04-schemas.md](04-schemas.md) into `schemas.py`. Add `POST /voyages` returning a hard-coded `VoyageState` fixture. | Write the Agent 1 system prompt. Test it on a hand-typed sample CP excerpt to validate extraction shape. | Three-panel layout: top bar, three columns. shadcn `Card`, `Table`, `Button` installed. |
| 30–60  | Add `GET /voyages/{id}`. Wire `InMemoryStore`. Stage the pipeline orchestrator with stubs. | Generate the Piraeus weather scenario v0 (HTML → PDF for the three docs). | Build `apiClient.ts`. Connect to A's mock endpoint. Render `DocumentCard` × 3 from the hard-coded `VoyageState`. |
| 60–90  | Write `pipeline.run()`: calls stubs for now, fills `VoyageState` stage by stage. | Plug in real Anthropic SDK call for Agent 1. Test against the scenario PDFs. | `LaytimeTable` and `QuantumDisplay` against the hard-coded data. `AgentSteps` component animating. |

By minute 90 (11:15):
- Frontend is fully laid out against a fake `VoyageState`.
- Backend has the route surface and the orchestrator skeleton.
- Agent 1 is doing real work on the scenario PDFs.
- The schemas have not changed since minute 30 — **freeze them**.

Everything from minute 90 onward is filling in the agents and polishing.

---

## 5. Tooling choices and why

| Tool                  | Why we picked it                                                                                    |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| `uv`                  | Fastest Python package manager. Hackathon-friendly install times. Drop-in for pip.                  |
| `pnpm`                | Fast, deterministic Node installs. Workspaces if we want them.                                      |
| `ruff`                | Lint + format in one binary. Zero config.                                                           |
| Pydantic v2           | The contract. Generates JSON schema for Anthropic tool-use. Plays with FastAPI.                     |
| FastAPI               | Async-first. Auto-generated OpenAPI docs. Pydantic-native. Best Python web framework for this shape.|
| Anthropic SDK         | Tool-use with `strict: true`. Prompt cache. Text input (pdfplumber upstream).                       |
| `pdfplumber`          | Local PDF text + table extraction (input docs). MIT, pure Python — no native deps.                  |
| `html2pdf.js`         | **Client-side** claim-letter PDF export from the rendered HTML. No server-side PDF lib, no cairo/pango. |
| `weasyprint` (dev-only)| Generates the synthetic *input* PDFs once, on a Mac/WSL. Never ships to the product runtime.        |
| AWS Amplify Hosting   | Next.js frontend deploy. Sponsor-aligned. SSR-capable. The "live on AWS" URL.                       |
| AWS App Runner        | FastAPI backend deploy. Container, scales to zero. Clean `python:3.12-slim` image.                  |
| Next.js 15 App Router | Default-good performance. Server components for static parts, client for the polling UI.            |
| `tailwindcss`         | Speed-of-thought styling. Mobile-responsive without custom CSS.                                     |
| `shadcn/ui`           | Components we own, not a dependency. Sensible defaults. Replaces a week of design work.             |
| `react-query` (TanStack)| Polling, caching, retries. Cleaner than `useEffect` for the pipeline status.                      |
| `zod`                 | Runtime validation of API responses on the frontend. Matches Pydantic on the backend.               |
| `lucide-react`        | Icons. Free, tree-shakable.                                                                         |
| `cmdk` (via shadcn)   | Command palette if we add one (stretch tier).                                                       |
| Supabase (Phase C only)| Auth + Postgres + Storage in one vendor. Runs on AWS. Fastest path to a complete product post-hackathon. |
| SQLAlchemy + Alembic  | Phase C. Migrations matter the moment we have data (against Supabase Postgres).                      |

---

## 6. Repo layout (write this down once, never refactor it)

```
portside/
├── README.md
├── notes/                          ← planning docs (this dir)
│   ├── 00-PLAN.md
│   ├── 01-domain-primer.md
│   ├── 02-architecture.md
│   ├── 03-agents.md
│   ├── 04-schemas.md
│   ├── 05-synthetic-data.md
│   ├── 06-frontend.md
│   ├── 07-day-plan.md
│   ├── 08-demo-and-pitch.md
│   └── extended_plan.md            ← this file
├── apps/
│   ├── api/                        ← FastAPI
│   │   ├── pyproject.toml
│   │   ├── portside_api/
│   │   │   ├── main.py             ← FastAPI app + routes
│   │   │   ├── pipeline.py         ← orchestrator
│   │   │   ├── schemas.py          ← Pydantic models
│   │   │   ├── storage.py          ← VoyageStore Protocol + implementations
│   │   │   ├── auth.py             ← Phase C: Supabase JWT verifier (no-op in Phase A)
│   │   │   ├── settings.py         ← pydantic-settings
│   │   │   ├── agents/
│   │   │   │   ├── extractor.py
│   │   │   │   ├── calculator.py
│   │   │   │   ├── analyst.py
│   │   │   │   └── drafter.py
│   │   │   ├── prompts/            ← .md files loaded at import
│   │   │   └── letter_template.html
│   │   └── tests/
│   │       └── test_calculator.py  ← the only Phase A test (the math must be right)
│   └── web/                        ← Next.js
│       ├── package.json
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   └── voyages/[id]/page.tsx
│       ├── components/
│       ├── lib/
│       │   ├── api.ts              ← typed fetch client
│       │   └── types.ts            ← zod schemas mirroring Pydantic
│       └── tailwind.config.ts
├── infra/                          ← Phase C only
│   ├── README.md
│   ├── api.Dockerfile
│   └── apprunner.yaml
├── synthetic-data/
│   ├── generate.py
│   └── scenarios/
└── .env.example
```

Two apps, one shared notes dir. No monorepo tooling (Turborepo / Nx) — `cd` is the build system.

---

## 7. API surface (frozen by 10:45 on May 28)

```
Phase A:
POST   /voyages                       multipart: cp, nor, sof, perspective  → 201 { voyage_id }
GET    /voyages/{id}                  → VoyageState (includes the letter HTML/segments)
POST   /voyages/{id}/revise           inline-revision micro-agent (Tier 1 stretch; see 13-inline-revision.md)
GET    /healthz
(no /letter.pdf or /letter.docx — PDF/Word are generated client-side from the letter HTML)

Phase C additions:
GET    /voyages                       (list, scoped to authed user)        → list[VoyageSummary]
DELETE /voyages/{id}
POST   /voyages/{id}/letter/email     send via SES
GET    /voyages/{id}/timebar          countdown + warnings
GET    /me                            current user (from Supabase JWT)
```

Every Phase C addition is purely additive. No Phase A endpoint changes.

---

## 8. Auth strategy

### Phase A — none
No auth. The app is local. Skip every middleware. CORS allows `http://localhost:3000`.

### Phase C — Supabase (auth + Postgres + storage in one)
- **Supabase bundles auth, a Postgres database, and object storage** — one signup, one vendor, instead of wiring Clerk + RDS + S3 separately. Fastest path to a complete-feeling product the week after the hackathon.
- Frontend: `@supabase/supabase-js` + `@supabase/ssr` for Next.js. Email/password + magic link out of the box.
- Backend: a FastAPI dependency that verifies the Supabase JWT (standard JWT, `SUPABASE_JWT_SECRET`) on every request and attaches the `user_id`. ~30 lines.
- Persistence: the `PostgresStore` implementation of the `VoyageStore` protocol points at Supabase Postgres. Voyage documents go to Supabase Storage. All `VoyageState` records carry `owner_user_id`; row-level security scopes by user.
- Free tier covers our launch (50,000 MAU, 500MB DB, 1GB storage).

Why Supabase over Clerk + RDS + S3:
- One vendor, one set of keys, one afternoon — versus three integrations.
- It **runs on AWS** under the hood, so the "powered by AWS" sponsor narrative still holds.
- JWTs are standard, so migrating off later (e.g., to Cognito if we ever want pure AWS-native) is low-cost.
- The AWS-native alternative — RDS Postgres + Cognito + S3 — is the fallback if we want zero third-party vendors, but Cognito is fiddly and slower to stand up. Not worth it for a contest sprint.

---

## 9. Stretch tiers — what moves the needle if we finish early

Each item is a self-contained 30–90 minute landing. Tier order is by **judge-perceived impact per hour invested**.

### Tier 1 — if we finish the MVP by 15:30
Land all of these. They turn a strong demo into a remarkable one.

1. **Inline highlight-and-revise on the letter and the narrative.** The highest-leverage stretch in this list. Selecting any line in the BIMCO claim letter or dispute narrative reveals a **Refine** toolbar — quick-action chips (More formal / Less aggressive / Add citation / Shorten) plus a freeform instruction box plus a manual-edit fallback. Adds a full demo beat ("the professional in the loop"). Full spec in [13-inline-revision.md](13-inline-revision.md). **Build this first.**
2. **Charterer-side rebuttal toggle.** The same pipeline, opposite perspective. Agent 3 prompt already accepts a `perspective` parameter. Worth doing because the most common follow-up question from a maritime judge is "great, but what if I'm the charterer being claimed against?" — having the answer pre-built is decisive.
3. **Time-bar countdown badge that goes red.** Already designed for the top bar. Compute days from `today` to `time_bar_date`. Three colors: green, amber, red. This is the single most credible-feeling moment in the UI.
4. **Excel export of the laytime table.** Claims executives live in Excel. `openpyxl`, one endpoint, 40 lines. A maritime judge will absolutely click "Download .xlsx" and respect it.

### Tier 2 — if we finish the MVP by 16:30
Pick two.

4. **A fleet view at `/`.** A list of seeded voyages with status, vessel, port, time-bar countdown. Click into one to see the detail page. We pre-seed 5 voyages from the backup scenarios. Suddenly Portside is "a product" not "a tool."
5. **Counterparty pattern insight.** A small inline panel on the right that says: "Mediterranean Crude Trading: 3 prior claims with this counterparty. Weather exception disputes upheld 2/3 times. Average settlement: 78% of claim quantum." Pre-seeded. The judge sees the "company brain" emerging.
6. **Side-by-side voyage comparison.** Show the current voyage next to a "precedent" voyage where the same dispute type was settled. Reinforces the dataset-moat story.

### Tier 3 — if we finish the MVP by 17:00 (unlikely, plan for the surprise)
Pick one.

7. **Greek-language UI toggle.** Tailwind makes this an i18n string-table swap. Symbolic — but the room is Athens.
8. **Gmail inbox monitoring (mocked).** Don't actually integrate Gmail. Build the UI: a "voyage being auto-assembled from your inbox" toast that detects when three documents land and prompts the user to open the voyage. We seed the data; the judge sees the future.
9. **Confidence-weighted negotiation outcome simulator.** Given the dispute analysis, show "expected settlement: USD 32,000 to 38,000 based on owner-position-strength and historical pattern." Two sentences of math. High judge appeal.

### What we do NOT stretch into
- Real Gmail integration. OAuth + token refresh + email parsing is a half-day in the best case.
- Real outbound email. SES has a sandbox to escape from.
- Real authentication. We rationalize "the demo is on a local laptop, why log in."
- Multi-port voyages. The domain model would need to expand.
- Time-charter support. Different domain entirely.

---

## 10. Phase C — taking Portside to the startup contest (the week after)

> **Note:** the hackathon-day deploy (Amplify frontend + App Runner backend, no auth/DB) is already done — see [02-architecture.md §12](02-architecture.md#12-hackathon-day-aws-deployment-parallel-flex-off-the-critical-path). Phase C *adds* persistence, auth, a custom domain, and CI/CD on top of that working deploy.

### Day 1 (May 29) — domain + infra bootstrap
- Buy `portside.app` or `portside.io` (~$15).
- Confirm the AWS account + $200 credit (already used for the hackathon Amplify/App Runner deploy).
- Create a **Supabase** project (auth + Postgres + storage). Copy the project URL, anon key, service-role key, and `SUPABASE_JWT_SECRET`.

### Day 2 (May 30) — persistence + auth
- Implement `SQLiteStore` first, locally, with Alembic migrations, then point `PostgresStore` at Supabase Postgres.
- Add the Supabase JWT verifier to FastAPI (~30 lines, `apps/api/portside_api/auth.py`).
- Add `@supabase/ssr` to the Next.js app: sign-in, sign-up, session. Move voyage document storage to Supabase Storage.
- Test end-to-end locally against the Supabase project.

### Day 3 (May 31) — promote the deploy
- App Runner already runs the backend from the hackathon. Add the new env vars (DATABASE_URL → Supabase, SUPABASE_JWT_SECRET) and redeploy.
  - Memory 1GB, vCPU 0.5, scale-to-zero. Estimated $5–15/month.
- Amplify already hosts the frontend. Add `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`, point `NEXT_PUBLIC_API_URL` at the App Runner URL, attach the custom domain.
- Turn on GitHub Actions autodeploy on push to `main` for both.

### Day 4 (June 1) — production polish
- Sentry: install both SDKs, free tier.
- CloudWatch alarms on App Runner 5xx rate.
- Seed three to five high-quality demo voyages from the backup scenarios into Supabase Postgres.
- Pre-record a 90-second product video for the contest deck.

### Day 5–7 — pilot conversations
- Reach back to the Greek shipping executive who validated the build.
- Ask: "what's the smallest version of this that you would pay $500/month for?"
- Iterate on that, not on what we imagine they need.

### Cost budget for the first month
| Item              | Estimated cost                                     |
| ----------------- | -------------------------------------------------- |
| Domain (1 year)   | $15                                                |
| AWS Amplify Hosting | $0–5 (free tier covers low traffic)              |
| AWS App Runner    | $10–20 (scales to zero between requests)           |
| Supabase          | $0 (free tier: auth + Postgres + storage)          |
| SES (Phase C+)    | <$1 (we are not sending many emails yet)           |
| Sentry            | $0 (free tier)                                     |
| Anthropic API     | usage-dependent. ~$0.05–0.10 per voyage on Sonnet 4.6 + pdfplumber. Budget $10/mo for early demos. |
| **Total infra**   | **~$35/mo** — comfortably inside the $200 credit for the first quarter |

---

## 11. Mobile / responsive approach

The three-panel desktop UI doesn't fit a phone. The strategy:

- **Tailwind breakpoints.** At `md:` and above, three columns. Below `md:`, panels collapse to a vertical tab switcher: **Docs | Calculation | Claim**, with the quantum always sticky at the bottom.
- **Same React components.** No mobile-specific re-render. We just change layout via classes.
- **Don't optimize for mobile during the hackathon.** Spend zero minutes on it on May 28th. Tailwind responsiveness gets us 80% there for free. Polish in Phase C.

What we do not build for mobile:
- Drag-and-drop upload. Mobile users tap a button and pick from the file picker.
- The contested-row inline expansion shows below the row on mobile, not inline.

---

## 12. Anti-patterns — what we will not do

- **Don't refactor across the integration boundary mid-day.** The schemas are the contract.
- **Don't write tests we don't need.** One test file: `test_calculator.py`. The math must be right. Everything else is throwaway.
- **Don't generalize the agents.** Four hard-coded agents. No "agent runner framework." We are not LangChain.
- **Don't introduce a queue.** Pipeline runs in one process, in one async coroutine, in 45 seconds.
- **Don't build a settings page.** Two environment variables. That is the configuration surface.
- **Don't write a database migration during the hackathon.** Phase A is in-memory. Migrations are Phase B/C.
- **Don't deploy during the hackathon.** Deploy is May 31.
- **Don't argue about whether to do something on May 28th.** Reread this doc. If it isn't in here, it's not happening.

---

## 13. Where to start, right now

Before the hackathon morning:

- [ ] Confirm `ANTHROPIC_API_KEY` works on at least two laptops with Sonnet 4.6 (and Opus 4.7 reachable as escape hatch).
- [ ] Decide who is Engineer A, B, C. Print or screenshot section 4 of this doc.
- [ ] Each engineer installs: `uv`, Python 3.12, Node 22, `pnpm`. Clone the repo.
- [ ] Read [00-PLAN.md](00-PLAN.md), [01-domain-primer.md](01-domain-primer.md), and the relevant track's spec.
- [ ] Sketch the demo PDF layout in HTML the night before (it's the easiest pre-work, and an hour saved on May 28th is worth two later in the day).
- [ ] On the morning of: arrive at 08:00, set up at one table, do not split rooms.

The first 10 minutes of the build window (09:45 – 09:55) are not for typing. They are for re-reading section 4 of this doc out loud as a team. Then everyone types.

---

## 14. Decision log (commit decisions here as we make them, not in chat)

| Date  | Decision                                      | Owner | Rationale                                            |
| ----- | --------------------------------------------- | ----- | ---------------------------------------------------- |
| 05-26 | Stack: FastAPI + Next.js + Anthropic Sonnet 4.6 + pdfplumber | team  | Best agent ergonomics + ~15–30× cheaper per voyage than Opus + native PDF, with no demo-quality loss on our text-native synthetic data |
| 05-26 | Demo scenario: Piraeus weather dispute        | team  | Lands in Athens; clean "aha" with $22k incremental   |
| 05-26 | No auth on May 28; Supabase in Phase C        | team  | Cuts an hour of integration risk from the hackathon  |
| 05-26 | Storage: in-memory → SQLite → Supabase Postgres| team  | Same `VoyageStore` Protocol; one-line swap each step |
| 05-28 | Deploy target: **AWS Amplify (frontend) + App Runner (backend)**, local demo stays primary | team  | AWS is the hackathon sponsor — Amplify over Vercel for sponsor credit + a live URL; deploy is a parallel flex, never on the critical path |
| 05-28 | PDF export is **client-side** (`html2pdf.js`); weasyprint kept dev-only for synthetic input PDFs | team  | Removes native cairo/pango deps everywhere — clean App Runner image, no GTK install on the Windows box |
| 05-28 | Phase C auth+DB: **Supabase** (not Clerk+RDS) | team  | One vendor for auth+Postgres+storage, runs on AWS, fastest path to a complete product for the contest |
| TBD   | Engineer track assignments (A / B / C)        | —     | Decide on the morning of May 28                      |
| TBD   | Exact demo dollar figures (38,400 vs 35,000)  | —     | Lock when generating the scenario PDFs               |
| TBD   | Domain name                                   | —     | Buy May 29                                           |
