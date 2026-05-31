# Laytimely — System of Record

> **Bucket 1 of 3. This is the single source of truth for everything that has
> been built.** If a feature is described here, it exists in the codebase on
> this branch. Forward-looking work lives in [ROADMAP.md](ROADMAP.md); how to
> run and ship it lives in [OPERATIONS.md](OPERATIONS.md). See
> [README.md](README.md) for the scoping rule that keeps these three from
> overlapping.
>
> Last consolidated: 2026-05-31, against `feat/w0-w1-analyst-citations-and-xlsx-button`
> (PR [#31](https://github.com/retryoos/portside/pull/31)). When the system
> changes, update this file rather than adding a parallel doc.

---

## 1. What Laytimely is

**Laytimely turns a contested port call into a ready-to-send demurrage
resolution in minutes.** Upload three voyage documents (Charter Party excerpt,
Notice of Readiness, Statement of Facts), choose the owner or charterer
perspective, and a four-agent pipeline returns a per-event laytime calculation,
the contested events with cited arguments and a strength rating, the claim
quantum in EUR, a formal BIMCO-style claim letter, and a time-bar date.

Built at the Florent x Panathēnea Hackathon (Athens, 28 May 2026) as
**Papership.Ai**, since rebranded to **Laytimely** (domain `laytimely.com`).
The Python package is still named `portside_api`; the product name is
Laytimely.

> The demo voyage (MT Aegean Pioneer, Ras Tanura to Rotterdam) runs end to end
> to `stage=done` with `demurrage_due_eur = 84,375.00`, locked by
> `tests/test_calculator.py`.

---

## 2. The core pipeline (the original four agents)

`POST /voyages` returns a `voyage_id` immediately and runs the pipeline in the
background, writing each stage to the store so the UI animates live progress:
`extracting -> calculating -> analyzing -> drafting -> done`.

```
three PDFs + perspective
        |
   pdf.py (pdfplumber local text + table extraction)
        |
 Agent 1  Extractor   (agents/extractor.py)  Sonnet 4.6 strict structured output -> ExtractionResult
        |
 Agent 2  Calculator  (agents/calculator.py) 2a classify events (LLM) -> 2b sum hours (deterministic Python) -> LaytimeResult
        |
 Agent 3  Analyst     (agents/analyst.py)    Sonnet 4.6 -> DisputeAnalysis (citations, strength, incremental EUR)
        |
 Agent 4  Drafter     (agents/drafter.py)    Sonnet 4.6 -> ClaimPacket (BIMCO letter + narrative)
        |
   VoyageState (orchestrated by pipeline.py, polled by the UI)
```

- **The arithmetic is deterministic Python, never the model.** The LLM
  classifies each Statement-of-Facts event; a plain Python function walks the
  timeline, sums hours, splits the row where the allowance is exhausted, and
  multiplies by the rate. Reproducible and auditable.
- **One model, four agents.** Sonnet 4.6 by default; Opus 4.7 is a per-agent
  quality escape via `ANTHROPIC_MODEL_PRIMARY` / `ANTHROPIC_MODEL_ESCAPE`.
  Shared Anthropic helpers and prompt caching live in `agents/llm.py`; tool
  definitions in `agents/tools.py`. A cross-cutting prompt prefix
  (`prompts/cross_cutting.md`) suppresses AI tells and enforces EUR, clause-by-
  number, and event-by-id formatting.
- **Graceful fallback.** If a PDF cannot be parsed the pipeline serves the
  canonical demo voyage (`fixtures.py`) rather than failing.
- **Inline revision.** `reviser.py` + `POST /voyages/{id}/revise` rewrite a
  highlighted sentence in the letter through a micro-agent, behind a server-side
  safety gate that rejects any rewrite changing a monetary value or dropping a
  clause/event reference.

---

## 3. Subsystems built on top of the core

Everything below was built after the hackathon MVP (the "weeks 5-8" waves and
the W0-W10 series). All of it is on this branch with tests.

### 3.1 Legal citation subsystem (`legal/`, `analyst_citations.py`)

The analyst cites the claim letter with **verified authorities** only: a
citation field is rejected at the schema layer unless it carries a
`verified_via_tool` flag returned by a real lookup. Sources:

- `legal/corpus.py` — a committed corpus of standard clauses and authorities.
- `legal/imo.py` — IMO conventions.
- `legal/eur_lex.py` — EUR-Lex / CELLAR client, gated by `LEGAL_EUR_LEX_LIVE`
  (off by default; corpus + IMO are the offline sources).
- `legal/verify.py` — the verification step that stamps `verified_via_tool`.
- `legal/outbound.py` — the single egress adapter (log + rate-limit + cache)
  that every outbound legal lookup goes through (default-deny on egress).
- `analyst_citations.py` — wires verified authorities into the analyst output.
- Frontend: `CitationFootnotes.tsx`, `AuthoritiesList.tsx`,
  `lib/letter-citations.ts`, and a Cases section in the Sources tab.

### 3.2 Claim strength sub-scores (`claim_strength.py`)

Beyond the single Strong/Arguable/Weak label, `FlaggedEvent` carries named
sub-scores: `clause_clarity`, `evidence_completeness`,
`counterparty_pushback_risk`, `time_bar_risk`. Surfaced as words (not fake
percentages) in `StrengthPanel.tsx` on contested-row expand.

### 3.3 Evidence checklist (`evidence_checklist.py`)

Lists every supporting document the recipient should receive and flags any not
yet attached, making the pack ship-ready rather than draft-ready. Surfaced in
`EvidenceChecklistTab.tsx`.

### 3.4 Both-sides defense (`defense.py`)

Defend against an incoming claim, not just file one: a charterer rebuttal with a
recomputed quantum. Rides the existing `Perspective = owner | charterer` thread
and `FlaggedEvent.charterer_argument`.

### 3.5 Research agent (`researcher.py`)

A tool-using agent fetches outside evidence (weather, port calendars) to back
disputed hours. Serves a committed offline fixture by default; `RESEARCH_LIVE=1`
is the seam for a live weather/calendar feed.

### 3.6 Exports

- **Excel** — `exports/excel.py`, `GET /voyages/{id}/laytime.xlsx` via
  `openpyxl` (pure Python, no native deps). Three sheets: Calculation, Summary,
  Letter. Snapshot-tested against the Rotterdam fixture. Button:
  `ExportXlsxButton.tsx`.
- **Word** — client-side `.docx` from the live letter DOM
  (`components/letter-to-docx.ts`, `ExportDocxButton.tsx`).
- **PDF** — client-side via `html2pdf.js` (`ExportPdfButton.tsx`).

### 3.7 Email send (`email/`)

- `email/ses.py` — send the finished claim letter via AWS SES. Gated by
  `EMAIL_SEND_LIVE` (default off: dev exercises a sandbox path that writes an
  audit row, rate-limits, and returns 200 with no outbound).
- `email/invitations.py`, `email/models.py` — workspace invitation emails.
- Frontend: `EmailLetterModal.tsx`, `EmailLetterButton.tsx`,
  `RecipientChipsInput.tsx`, plus a `MailtoLetterButton.tsx` fallback.

### 3.8 Email-in ingestion (`inbox/`, `inbox_address.py`)

A unique inbox address per workspace (`<slug>@<INBOX_DOMAIN>`, default
`in.laytimely.com`). Forwarded SoFs/CPs/NORs/correspondence are parsed, matched
to a voyage (or open a new one), and surfaced.

- `inbox/parser.py` (MIME), `inbox/matcher.py` (voyage matching),
  `inbox/signature.py` (the SES -> S3 -> Lambda hop signs payloads with
  `EMAIL_IN_SHARED_SECRET`; the inbound route fails closed when unset),
  `inbox/models.py`.
- `inbox_address.py` + `GET /workspaces/{id}/inbox-address`.
- Frontend: `CorrespondenceTimeline.tsx`, `settings/inbox` page,
  `InboxSetupCard.tsx`.

### 3.9 Multi-tenant workspaces (`workspaces.py`)

Members, roles (owner/admin/member/viewer), workspace-scoped voyages, and
invitations. Every voyage is owned by a `workspace_id`; the backend mints a
personal workspace per user so the data contract is consistent even when the
`WORKSPACES_UI` switcher is hidden (default off).

- Frontend: `settings/members` + `MembersTable.tsx`, `settings/invitations` +
  `InvitationForm.tsx` / `InvitationsTable.tsx`, `invite/[token]` accept page,
  `lib/use-active-workspace.tsx`.

### 3.10 Audit log (`audit.py`)

Append-only record of voyage create/delete, revise apply, claim send,
invitations, etc. Bounded by `AUDIT_RETENTION_DAYS` (default 90; reaped on
startup). Surfaced on the `settings/audit` page via `AuditTable.tsx`.

### 3.11 Authentication (`auth.py` + web `lib/auth/`)

A JWT auth stub forward-compatible with AWS Cognito. `DEV_AUTH` (default on when
no Cognito pool is configured) returns a fixed dev user (`admin / admin`).
Setting `COGNITO_*` + `DEV_AUTH=0` turns on real JWKS verification with **no
backend code change** (issuer/JWKS URLs derived in `settings.py`).

- Web: `lib/auth/credentials.ts`, `lib/auth/session.ts`,
  `lib/auth/constants.ts`; same-origin routes `api/auth/{login,logout,me,token}`;
  `middleware.ts`. The browser calls the API directly, so the API is the real
  auth boundary; `lib/api.ts` is a central `apiFetch` that attaches the Bearer
  token and retries once on 401.

---

## 4. Persistence and storage

- **Store:** `storage.py` defines `SqlStore` (SQLAlchemy async, survives
  restart, Postgres-ready) and `InMemoryStore` (tests + offline). The SQL store
  is the default; `InMemoryStore` is monkeypatched in by tests.
- **Database:** `db/engine.py`, `db/models.py`, `db/mapping.py`. Default
  `DATABASE_URL` is a local SQLite file (`portside.db`); production sets it to
  Postgres (`postgresql+asyncpg://...`).
- **Migrations:** Alembic (`apps/api/alembic/versions/`), seven to date:
  `initial_schema`, `voyage_documents`, `voyage_evidence`, `audit_events`,
  `workspaces`, `voyage_citations`, `invitations_accepted_by`.
- **Object storage:** `objects.py` abstracts uploaded-PDF storage. Default is a
  local directory (`_objects/`); setting `S3_BUCKET` switches to S3 with **no
  code change**. A startup reaper (`STALE_RUN_SECONDS`, default 900) marks
  voyages stuck mid-pipeline as `error` (their driving task died with a prior
  instance).

---

## 5. API surface

```
GET  /healthz                          liveness
GET  /voyages                          list voyages (VoyageSummary)
GET  /vessels                          voyages grouped by vessel (VesselSummary)
POST /voyages                          multipart cp, nor, sof + perspective -> { voyage_id }
GET  /voyages/{id}                     current VoyageState (poll ~500 ms)
POST /voyages/{id}/revise              inline revision with server-side safety gate
GET  /voyages/{id}/laytime.xlsx        Excel export
POST /voyages/{id}/letter/email        send the claim letter via SES
... evidence-checklist, claim-strength, citations routes per their subsystems
GET  /workspaces/{id}/inbox-address    per-workspace email-in address
... workspace member + invitation routes
```

`POST /voyages` is rate-limited (`RATE_LIMIT_MAX_REQUESTS` / `_WINDOW_SECONDS`,
default 30/60s) as a cost guard, with an upload size cap (25 MiB/file) and a
`application/pdf` content-type allowlist. Security headers are applied on both
tiers; unexpected errors are logged server-side and returned generic.

---

## 6. Frontend

- **Next.js 15 (App Router), React 19, Tailwind v4** with a design-token theme
  (`apps/web/DESIGN.md` is the tokens contract). Fonts: Fraunces / IBM Plex Sans
  / JetBrains Mono. Editorial "Revolut-grade" visual direction (the R0-R8
  revamp).
- **Product routes:** `/` (redirect), `/cases` (dashboard), `/cases/[id]` (case
  detail with Sources/Calculation/Documents/Evidence tabs and client-side
  export), `/vessels` + `/vessels/[name]` (fleet view), `/claim` (new claim
  dropzone), `/revise`, `/login`, `/invite/[token]`, and
  `/settings/{members,invitations,audit,inbox}`.
- **Marketing site:** a `(marketing)` route group — landing page plus
  `/contact`, `/privacy`, `/security`, `/terms` — with its own nav/footer and
  components under `components/marketing/`.
- **Offline demo:** `lib/demo.ts` mirrors `fixtures.py` so "Try the demo voyage"
  renders end to end with no backend call.

---

## 7. Configuration (feature-flag surface)

All config is environment-driven (`settings.py`). The flags that gate built-but-
dormant capability:

| Var | Default | Effect |
| --- | --- | --- |
| `DEV_AUTH` | on if no Cognito pool | bypass JWT, fixed dev user |
| `COGNITO_REGION/USER_POOL_ID/CLIENT_ID` | unset | turn on real JWKS auth |
| `DATABASE_URL` | local SQLite | Postgres in prod |
| `S3_BUCKET` / `S3_REGION` / `S3_PREFIX` | unset | object storage to S3 |
| `RESEARCH_LIVE` | off | live weather/calendar feed vs offline fixture |
| `LEGAL_EUR_LEX_LIVE` / `LEGAL_BAILII_LIVE` | off | live legal lookups |
| `EMAIL_SEND_LIVE` | off | real SES send vs sandbox path |
| `EMAIL_IN_SHARED_SECRET` | unset (fail closed) | inbound email signing |
| `INBOX_DOMAIN` | `in.laytimely.com` | per-workspace inbox addresses |
| `WORKSPACES_UI` | off | show the workspace switcher |
| `RATE_LIMIT_*`, `AUDIT_RETENTION_DAYS`, `INVITATION_RATE_LIMIT_*` | see `settings.py` | guards/retention |
| `SES_SENDER`, `INVITATION_BASE_URL` | unset / localhost | invitation email path |
| `ANTHROPIC_MODEL_PRIMARY/ESCAPE`, `REQUEST_TIMEOUT_S`, `CORS_ORIGINS` | Sonnet 4.6 / Opus 4.7 / 30s / localhost | model + transport |

---

## 8. Tests

`apps/api/tests/` covers each subsystem: `test_calculator` (the EUR 84,375 gate),
`test_analyst_citations`, `test_citations_route`, `test_audit`, `test_auth`,
`test_defense`, `test_email_send`, `test_evidence_and_strength` +
`test_evidence_checklist_route` + `test_strengths_route`, `test_excel_export` +
`test_export_demo_fixture`, `test_inbox` + `test_inbox_address`,
`test_legal_subsystem`, `test_main_async`, `test_objects` + `test_reaper`,
`test_prompts`, `test_research`, `test_revise_apply` + `test_reviser`,
`test_settings`, `test_sql_store` + `test_storage`, `test_upload_limits`,
`test_workspaces` + `test_workspace_member_routes` +
`test_workspace_invitations_route`. Frontend unit tests via Vitest
(`lib/flags.test.ts`, `lib/letter-citations.test.ts`).

---

## 9. Repository layout

```
apps/
  api/                         FastAPI backend (package: portside_api)
    portside_api/
      main.py                  routes + async background pipeline
      pipeline.py              orchestrator
      pdf.py                   pdfplumber extraction
      agents/                  extractor, calculator, analyst, drafter, llm, tools
      prompts/                 role prompts + cross_cutting prefix
      schemas.py               frozen Pydantic VoyageState contract
      storage.py               SqlStore + InMemoryStore
      db/                      engine, models, mapping (SQLAlchemy async)
      objects.py               filesystem / S3 object store
      fixtures.py              canonical demo voyage
      reviser.py               inline revision + safety gate
      analyst_citations.py, legal/    verified-citation subsystem
      claim_strength.py, evidence_checklist.py, defense.py, researcher.py
      exports/excel.py         Excel laytime export
      email/                   SES send + invitations
      inbox/, inbox_address.py email-in ingestion
      workspaces.py            multi-tenant workspaces + invitations
      audit.py                 append-only audit log
      auth.py                  JWT stub, Cognito-ready
      limits.py                rate limit + upload limits + security headers
      settings.py              env-driven config
    alembic/                   migrations
    tests/                     full subsystem coverage
    Dockerfile, apprunner.yaml deploy artifacts (see OPERATIONS.md)
  web/                         Next.js 15 frontend
    app/                       product routes + (marketing) group + api/auth
    components/                product + marketing + settings components
    lib/                       api client, auth, demo fixture, formatting, flags
    DESIGN.md                  design tokens contract
synthetic-data/                demo PDF generator + committed scenario PDFs
notes/                         SYSTEM.md (this) · ROADMAP.md · OPERATIONS.md · README.md
```
