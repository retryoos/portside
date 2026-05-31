# Architecture plan — weeks 5 to 8

> Production-grade architecture for the work that follows the founder's
> personal weeks 1 to 4 (deploy, rename, Cognito, Sentry). Two waves,
> each a coherent set of features that ship together. Local dev first;
> deploy when production-ready.
>
> Weeks 5 to 6: completes the demurrage offering. Excel, Word, email,
> evidence checklist, claim strength sub-scores, and a legal precedence
> citation subsystem.
>
> Weeks 7 to 8: the platform that turns a single-user demo into a
> service: multi-tenant workspaces, audit log, email-in ingestion.

---

## 0. Guiding principles

These apply across both waves; do not relitigate per feature.

1. **Backend over frontend for anything legal or financial.** The
   claim letter, the EUR figures, the citations: every byte must
   round-trip a backend that can audit them. Browser-only exports are
   client-side conveniences, not source of truth.
2. **The arithmetic is never in the model.** Already the rule for
   laytime; we extend the rule to: time-bar math, evidence-completeness
   booleans, swing calculations, and the FuelEU intensity math (later).
3. **The agent never invents a citation.** A new structured-output
   discipline: a citation field is rejected at the schema layer unless
   it carries a `verified_via_tool: bool` flag returned by a real tool
   call.
4. **Feature-local wire models** to keep `schemas.py` and
   `lib/types.ts` frozen except for explicitly announced additions.
   We extend `FlaggedEvent` and `ClaimPacket` once each in this wave,
   announced ahead of time.
5. **Default deny on egress.** Any new outbound call (SES, EUR-Lex,
   BAILII) goes through a single `outbound.py` adapter that logs +
   rate-limits + caches.
6. **Production readiness checklist before deploy** (section 6).
   Every feature in this plan is built locally first; the deploy
   button is the very last step.

---

## 1. Week 5 to 6 — completing the demurrage product

### 1.1 Excel laytime export (`/voyages/{id}/laytime.xlsx`)

**Why backend.** The Excel file is an artifact a customer mails to
arbitrators and counterparties; a deterministic, audited output is
non-negotiable. Backend ensures the same workbook drops out for any
caller of the API, including the public-API consumer in section 2.5
of [product_roadmap.md](product_roadmap.md).

**Stack.** `openpyxl` (pure Python, no native deps; fits the
`python:3.12-slim` App Runner image untouched). Reject `xlsxwriter`:
similar features, slightly faster, but the discovery surface (cell
formats, conditional formatting, etc.) is smaller and we want the
optionality.

**File layout.**

```
apps/api/portside_api/
  exports/
    __init__.py
    excel.py          # render_laytime_workbook(voyage) -> bytes
  routes/
    exports.py        # GET /voyages/{id}/laytime.xlsx
```

**Workbook structure.** One file, three sheets:

- `Calculation`: the laytime ledger. Columns: Timestamp, Description,
  Category (Laytime / Excepted / Demurrage), Duration h, Cum h,
  Status. Contested rows fill in `warning-container` colour. Right-
  align numeric columns. Tabular nums.
- `Summary`: the key/value strip from `LaytimeSummary.tsx`: laytime
  allowed, used, on demurrage, rate, demurrage due, despatch due (if
  any).
- `Letter`: a flat dump of `packet.claim_letter_markdown` rendered as
  plain text. For lawyers who want the letter alongside the math in
  one file.

**Determinism.** Cell formats hard-coded by ISO date format and the
`#,##0.00` currency mask; no model output enters the workbook
verbatim except via the snapshotted `claim_letter_markdown`. Snapshot
test in `tests/test_excel.py` against the Rotterdam fixture: open the
workbook, assert sheet count = 3, assert `Summary!B5 == 84375.0`.

**Acceptance.** `GET /voyages/v_demo/laytime.xlsx` returns a 200 with
`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
and a workbook that passes the snapshot test.

---

### 1.2 Word export (`.docx`)

**Why client-side.** The letter is already `contentEditable` in
`ClaimLetter.tsx`. Edits made in the browser flow into the export the
same way the PDF export captures the live DOM. A backend export would
re-render from `claim_letter_markdown` and silently strip the edits;
unacceptable. Mirror the PDF pattern: capture the DOM, transform to
docx, download.

**Stack.** [`docx`](https://www.npmjs.com/package/docx) (the
`Document/Paragraph/TextRun` API). Add the dependency only to
`apps/web`. Reject `html-to-docx` (worse output for nested lists) and
`mammoth` (wrong direction; mammoth converts docx -> html).

**File layout.**

```
apps/web/components/
  ExportDocxButton.tsx       # sits next to ExportPdfButton
  letter-to-docx.ts          # pure function: HTMLElement -> Blob (docx bytes)
```

**Approach.** Walk the live letter DOM in the same target id as the
PDF export (`LETTER_DOM_ID`). Map elements:

- `p`, `h1`, `h2`, `h3` → `Paragraph` with style `Body`, `Heading 1`,
  `Heading 2`, `Heading 3`.
- `ul/ol/li` → `Paragraph` with `numbering: { reference: "default", level: n }`.
- `strong/em` → `TextRun` with `bold`/`italic`.
- Inline citations (a future custom element from section 1.6) → a
  `TextRun` with `superScript: true` plus a footnote.

**Filename.** `demurrage-claim-<vessel>-<YYYYMMDD>.docx`.

**Tests.** Vitest unit test that feeds the Rotterdam fixture HTML
through `letter-to-docx.ts` and reads back the resulting docx with
`mammoth` to compare to a golden Markdown.

**Acceptance.** A "Download Word" button next to the existing
"Download PDF" button on `/cases/<id>`. Both produce a file with the
on-screen letter contents, including any contentEditable edits.

---

### 1.3 Email send via SES

**Why backend.** Sending an external email IS the side effect that
needs audit, rate limit, and identity. Browser cannot do it.

**Stack.** `boto3` SES v2 client (already in the dependency tree for
S3). Sandbox-mode in dev: every recipient must be verified at SES.
Production access (general send) is a one-time AWS support ticket
that takes ~24 hours; gated behind a settings flag so we ship the
code first and flip the flag when SES approves us.

**File layout.**

```
apps/api/portside_api/
  email/
    __init__.py
    ses.py            # send_letter_email(voyage, to, cc, custom_body) -> ses_message_id
    templates/
      claim_letter.html.j2    # Jinja2; one column, brand wordmark, then the letter
  routes/
    email.py          # POST /voyages/{id}/letter/email
```

**Request and response.**

```
POST /voyages/{id}/letter/email
{
  "to": ["claims@charterer.com"],
  "cc": ["legal@us.com"],
  "subject": "Demurrage Claim, MT Aegean Pioneer ...",   // optional
  "preamble_markdown": "Dear Sirs, ..."                    // optional, prepended
}

200 { "ses_message_id": "...", "sent_at": "2026-..." }
```

**Output.** The email body is the rendered HTML (letter + sender
wordmark + a one-line footer). Attachments: the PDF (generated
server-side from `claim_letter_markdown` via `WeasyPrint`? No, the
client-side PDF lives only in the browser, so we either re-render or
ask the client to upload the PDF before sending). Approach: client
uploads the PDF blob alongside the POST as a multipart attachment;
backend forwards as-is. This preserves the "edits in the browser flow
to the recipient" property.

**Audit.** Every send writes an `audit_events` row (section 2.2) with
actor, voyage_id, recipient list, ses_message_id.

**Verification path before production.**

- Dev: SES sandbox, all to/cc must be on the verified-identity list.
- Pre-prod: stage `email-send-staging` with a single test address.
- Prod: SES production access flipped via Doppler; rate limit imposed
  at the route via slowapi (3/min per workspace).

**Acceptance.** Locally, with SES sandbox, sending to a verified
address produces a real email with the rendered letter and an
attached PDF. The audit row is written. Failures return 5xx with a
specific error code (`SES_THROTTLED`, `SES_UNVERIFIED_RECIPIENT`,
`SES_REJECTED`).

---

### 1.4 Evidence checklist

**Why now.** A claim letter without a list of attached documents looks
amateur. Today the packet has `supporting_documents: list[str]`, which
is just file names. Receivers want a checklist: what each document is,
which point in the letter it supports, whether it is attached.

**Schema change (announced, frozen-schema break).**

```
class EvidenceItem(BaseModel):
    role: Literal["cp_excerpt", "nor", "sof", "bunker_note", "port_log",
                  "weather_observation", "agent_correspondence", "other"]
    label: str            # human label, e.g. "Charter Party clause 14"
    supports_event_id: Optional[str] = None
    supports_clause: Optional[str] = None  # e.g. "Clause 14"
    attached: bool         # is the file actually in supporting_documents
    source_voyage_doc_id: Optional[str] = None
    note: Optional[str] = None  # one line of context for the recipient

class ClaimPacket(BaseModel):
    # ... existing fields ...
    evidence_checklist: list[EvidenceItem]
```

**Who fills it.** The drafter agent (Agent 4) emits the checklist as
part of `ClaimPacket`. Inputs: the `DisputeAnalysis.flagged_events`
(each has `evidence_required: list[str]`), the voyage's uploaded
documents (CP, NOR, SoF), any research-agent evidence from
[new_features/02-research-agents.md](new_features/02-research-agents.md).
The `attached` boolean is set deterministically post-call by checking
against `voyage.documents` and the research-agent bundle. The model
never owns the boolean.

**Surface.** A new "Evidence" tab in `SourcesTabs.tsx` next to
Sources / Calculation / Documents. Each row: label, role chip,
supports-link (clickable, scrolls the letter to the cited clause or
event), attached state (✓ / ✗).

**Tests.** A snapshot test that the Rotterdam case produces at least
three evidence items (CP clause 14, SoF event id of the weather
stoppage, the optional Rotterdam Port Authority weather record from
the research agent).

**Acceptance.** The checklist is rendered, the supports-links scroll
correctly, and unchecked items are visually flagged amber.

---

### 1.5 Claim strength sub-scores

**Why now.** `owner_position_strength: float` collapses too much into
one word. The recipient cannot tell why a flag is "Arguable" — is it
because the clause is weak, the evidence is thin, the counterparty
has precedent, or the time bar is closing? Sub-scores give the
internal team a triage view and the recipient a credible breakdown.

**Schema change (announced, frozen-schema break).**

```
Strength = Literal["Strong", "Arguable", "Weak"]

class ClaimStrengthSubScores(BaseModel):
    clause_clarity: Strength
    evidence_completeness: Strength
    counterparty_pushback_risk: Strength  # higher risk = weaker
    time_bar_risk: Strength                # closer to deadline = weaker

class FlaggedEvent(BaseModel):
    # ... existing fields ...
    sub_scores: ClaimStrengthSubScores
    # overall strength stays the existing owner_position_strength
```

**Who fills it.** The analyst agent (Agent 3) extended with one new
prompt section that asks for the four sub-scores explicitly. The
`time_bar_risk` is derived deterministically post-call from
`packet.days_until_time_bar` (closer than 14 days = Weak; closer than
45 = Arguable; > 45 = Strong). The model never owns time-bar arithmetic.

**Surface.** On the case detail right rail, a small "Strength" panel
appears when a contested row is open. Four labels, four words. No
percentages.

**Calibration plan (the soft part).** Until we have 50-100 labelled
historical claims, the four sub-scores are heuristic. Build the
schema and the agent prompt in this wave; collect labels with the
first three paying customers; recalibrate the prompt against the
dataset in a quarterly review.

**Tests.** A schema round-trip test, plus a prompt regression test on
the Rotterdam case (lock the four sub-scores against the fixture).

**Acceptance.** The four sub-scores render on screen and persist into
the PDF / Word export.

---

### 1.6 Legal precedence citation subsystem (the user's question)

**Why now.** Today the Rotterdam case cites *The Mexico 1 [1990] 1
Lloyd's Rep 507* in the analyst prompt as a fixed string. That works
for the demo voyage; it does not work for any other case. A serious
claim cites *the right case for this argument*. Without a real
citation system, the agent will hallucinate citations the moment the
prompt is asked for one outside the demo's scope.

**Architecture.**

```
                 +-----------------------------+
                 |       LegalCiteAgent         |
                 |  (Sonnet 4.6 tool-use loop) |
                 +-----------+-----------------+
                             |
       +---------------------+----------------------+
       |               |                |           |
   search_case_     lookup_case   search_eur_lex  lookup_imo_
   corpus           by_citation   (REST)          convention
       |               |                |           |
       v               v                v           v
   apps/api/portside_api/legal/
     corpus.jsonl                                  # curated 200-300 cases
     imo_conventions.json                          # public-domain texts
     eur_lex_client.py                             # thin wrapper + cache
     bailii_client.py        (Phase 2)             # scrape with cache + robots
```

**The curated corpus.** A JSONL file at
`apps/api/portside_api/legal/corpus.jsonl`. Each row:

```json
{
  "case_id": "the-mexico-1-1990",
  "citation": "The Mexico 1 [1990] 1 Lloyd's Rep 507",
  "court": "EWCA",
  "year": 1990,
  "topics": ["weather_exception", "laytime_stoppage", "notice_of_readiness"],
  "headnote": "An exception for weather stoppages requires the contractual condition (e.g. precipitation rate) to be met; the master's view alone is insufficient.",
  "url": "https://www.bailii.org/...",
  "free_full_text": false
}
```

Seed: ~150 most-cited UK demurrage / laytime / NOR cases, ~30 CJEU
cases on EU ETS / FuelEU / port-state control, ~20 Greek decisions
under the Code of Private Maritime Law (KIND), ~20 ICC awards via
public reports. Each row hand-reviewed.

**Tool 1 — `search_case_corpus(query, topic_filter=None) -> list[CaseHit]`.**
Full-text search over the JSONL using BM25 (rank_bm25 in Python, no
service). Returns top 5 with case_id, citation, headnote, score. Fast
and free.

**Tool 2 — `lookup_case(citation: str) -> Case | None`.** Exact
citation lookup. Returns the full row or None. The model uses this to
confirm a citation it remembers.

**Tool 3 — `search_eur_lex(query, doc_type) -> list[EurLexHit]`.**
Wraps the EUR-Lex public REST endpoints (CELLAR for documents,
SPARQL for metadata). Free; rate-limited at ~5 req/sec. Used for FuelEU /
EU ETS / CJEU citations. Cache the response per query for 30 days.

**Tool 4 — `lookup_imo_convention(name, article) -> str`.** Loads
from a committed `imo_conventions.json` with the verbatim text of the
public-domain IMO conventions we care about: SOLAS, MARPOL, MLC 2006,
Hague-Visby Rules. Returns the article text. No external call.

**Tool 5 (Phase 2) — `search_bailii(query) -> list[BailiiHit]`.**
Polite scraper of bailii.org with a 1 req/sec ceiling, respect for
robots.txt, full response cached for 30 days. Only used when the
curated corpus has no hit. Behind a settings flag (`BAILII_SCRAPE_OK`).

**Schema additions (in the analyst output, feature-local).**

```python
class CitedAuthority(BaseModel):
    citation: str                  # "The Mexico 1 [1990] 1 Lloyd's Rep 507"
    verified_via_tool: bool         # MUST be True for the schema to accept the field
    tool_used: Literal["corpus", "lookup", "eur_lex", "imo", "bailii"]
    proposition: str                # one-line summary of what we cite it for
    url: Optional[str] = None

class FlaggedEvent(BaseModel):
    # ... existing fields ...
    cited_authorities: list[CitedAuthority]
```

**The verification gate (the slop killer).** The route handler that
accepts the analyst's structured output runs a post-call validator:
every `CitedAuthority` with `verified_via_tool=True` must have its
`citation` actually present in the tool transcript that produced this
analyst run. Any unverified citation is dropped and a warning is
emitted. The model is told this in the prompt; if it cheats, the
schema rejects.

**Local dev.** The corpus JSONL ships in the repo; no network calls
needed for the most common queries. EUR-Lex is reachable from any
laptop; we cache aggressively. BAILII is off by default in dev.

**Production posture.** The corpus is versioned in git; quarterly
curation by the legal lead. EUR-Lex cache lives in Redis (managed
ElastiCache or a tiny instance) once we have it; until then it lives
in an in-memory LRU per process, which is fine for our volume.

**Acceptance.** Re-running the Rotterdam case through the new analyst
emits exactly one `CitedAuthority` for the weather argument, pointing
at *The Mexico 1*, with `verified_via_tool=True`, `tool_used="corpus"`,
and the headnote substring "precipitation rate" in `proposition`.

**Down the line.** This is the same shape the EU ETS / FuelEU
compliance product needs: it cites Regulation (EU) 2023/1805 article
4, Regulation (EU) 2015/757, etc. Same tool, same schema, same
verification gate. We are building the system once and reusing it.

---

### 1.7 Documentation we will need (the user's other question)

Per-feature documentation requirements before any one of these goes
to production:

- **Excel** ([1.1]). Internal doc in `notes/exports.md`: the column
  layout, the colour rules, the snapshot test target. One page.
- **Word** ([1.2]). Internal doc same file: the element mapping
  table and the "edits in browser flow through to docx" guarantee.
- **Email** ([1.3]). Three external documents we must consume and
  archive:
  1. **AWS SES sandbox vs production** (limits, throttling). Action:
     read once; gate the prod flip behind manual SRE sign-off.
  2. **CAN-SPAM / GDPR e-mail rules** (footer requirement, unsubscribe
     for commercial mail, sender identity). Action: bake the footer
     into the template; manual sends only, no marketing flow.
  3. **AWS support ticket template** for SES production access.
     Action: file once.
- **Evidence checklist** ([1.4]). No external docs; the schema
  comment is the spec.
- **Claim strength sub-scores** ([1.5]). No external docs; the
  prompt addition is the spec. Calibration set lives in a private
  Drive folder later.
- **Legal citation** ([1.6]). Three external sources to read once
  and bookmark:
  1. **BAILII robots.txt + scraping etiquette**.
  2. **EUR-Lex CELLAR API documentation** at https://op.europa.eu/en/web/cellar.
  3. **IMO public-domain conventions** (the full text PDFs).
- **Google Docs.** Not in this plan. Lawyers want Word; Google Docs
  needs an OAuth flow we do not yet need. Park it.

---

## 2. Week 7 to 8 — the platform that turns the demo into a service

### 2.1 Multi-tenant workspaces

**Why now.** Real teams need members, roles, per-workspace voyages,
and invitations. The single-user happy path stays the default so we
do not break the demo.

**Schema additions (announced, frozen-schema break).**

```
workspaces(id PK, name, plan, created_at)
memberships(id PK, workspace_id FK, user_sub, role, invited_at, accepted_at)
invitations(id PK, workspace_id FK, email, role, token, expires_at, accepted_at?)

voyages: add workspace_id FK (default = the inviter's personal workspace)
audit_events: add workspace_id FK
```

`role` is one of `owner` / `admin` / `member` / `viewer`. On every
read (`GET /voyages`, etc.) the route handler filters by
`workspace_id IN (memberships of current user)`.

**Migration shape.** A single Alembic migration that:

1. Adds the three new tables.
2. Adds `workspace_id` to `voyages` and `audit_events`, nullable for
   one release.
3. Backfills: every existing user gets a personal workspace named
   "<user.name>'s workspace"; every existing voyage gets that
   workspace's id.
4. A follow-up migration flips the column to NOT NULL.

**Feature flag.** `WORKSPACES_UI=1` env var on the frontend. While
off, the UI never shows the workspace switcher; the user has exactly
one workspace, theirs. Flip when ready.

**Invitations flow.** Token-based, like every other SaaS:

1. Workspace admin enters email + role on `/settings/members`.
2. Backend writes `invitations` row, sends an SES email containing a
   signed URL `https://laytimely.com/invite/<token>`.
3. Recipient lands on the page; if signed in to the matching email,
   button "Join workspace" calls `POST /workspaces/<id>/accept` and
   creates the membership; if signed out, the page kicks them through
   sign-in first with a `next=` redirect.
4. Token expires in 14 days, can be revoked from the admin page.

**Authorisation helper.** A FastAPI dependency
`require_workspace_role(min_role: Role)` that resolves the current
user's role in the workspace the request targets and 403s otherwise.

**Acceptance.** With `WORKSPACES_UI=1`, a workspace admin can invite
a teammate by email; the teammate signs in via the link and sees the
shared cases dashboard. A `viewer` cannot delete a voyage or send a
claim letter.

---

### 2.2 Audit log

**Why now.** Every product that touches money or legal documents
needs to answer "who did what when". Compliance, customer trust,
incident response.

**Schema additions.**

```
audit_events(
  id PK,
  workspace_id FK,
  actor_sub,                 # Cognito sub, or "system" for pipeline runs
  action,                    # "voyage.create" | "voyage.delete" | "letter.email" | ...
  target_type,               # "voyage" | "claim" | "membership" | ...
  target_id,
  at,                        # timestamp
  payload_redacted JSONB     # the minimal payload, with PII scrubbed
)
```

**Where the writes happen.** A single helper
`audit.record(action, target_type, target_id, payload)` called from
every route that mutates state. Decorator pattern is too clever;
explicit calls are easier to read in code review.

**Retention.** 90 days hot in Postgres; CloudWatch sink for the long
tail with year-long retention. SES-rate-limit-style: the table is the
fast lookup, CloudWatch is the long memory.

**UI.** A `/settings/audit` page for workspace admins. Pagination,
filter by actor, action, date range. Plain list, no fancy graphs.

**Acceptance.** Every existing mutation endpoint (`POST /voyages`,
`DELETE /voyages/{id}`, `POST /voyages/{id}/revise`, the new email
send and Word export) writes an audit row. The audit page renders the
last 100 events for the current workspace.

---

### 2.3 Email-in ingestion

**Why now.** The drag-and-drop UX gates daily use. Real ops teams
forward documents to a per-workspace inbox; the system should pick
them up automatically.

**Stack.**

- **Inbound mail receiver.** AWS SES inbound rules write the raw RFC
  822 message to S3 under
  `s3://laytimely-mail-inbound/messages/<workspace_id>/<message_id>.eml`.
- **Trigger.** S3 PutObject → AWS Lambda → `POST /voyages/from-email`
  on the App Runner backend.
- **Per-workspace addressing.** Each workspace gets an address
  `<workspace_id_short>@in.laytimely.com`. The MX record points at
  SES.

**The from-email route.**

```
POST /voyages/from-email
  X-SES-Verified-Domain: laytimely.com
  X-SES-Signature: <hmac>          # verified at the boundary
  body: multipart with the raw .eml

  -> 202 { "voyage_id": "...", "matched": "existing" | "new" }
```

The route:

1. Verifies the SES signature and the source bucket.
2. Parses the MIME with `mailparser` (stdlib `email` is fine).
3. Extracts attachments. Only `application/pdf` accepted; size cap
   25 MB (same as the API upload cap).
4. Runs ClamAV on the attachments (Lambda layer); 400 if any hit.
5. Tries to match an existing voyage by subject-line tagging
   (`[V-12345]`) or by sender domain + recent context. If no match,
   creates a new voyage.
6. Enqueues the pipeline run as today, returns 202 immediately.

**Security posture.**

- SES inbound configured with **SPF / DKIM / DMARC** enforcement; a
  failure marks the message Spam and we drop it.
- ClamAV scans every attachment; failed scan = drop, log, no voyage
  created.
- 25 MB cap per message; SES rejects bigger. No archives, no scripts,
  no Office macros (drop `.docm`, `.xlsm`).
- Per-workspace rate limit (50 messages per hour) at the route, via
  slowapi keyed by `workspace_id_short`.

**Local dev posture.** Without SES, run a tiny SMTP server in
`apps/api/scripts/dev_smtp.py` that reads stdin and posts to the
local backend with the same `X-SES-Verified-Domain` header signed with
a dev secret. End-to-end flow testable on a laptop.

**Acceptance.** Sending an email to the dev SMTP with a CP, NOR, SoF
PDF attached creates a voyage with the three docs attached, runs the
pipeline, lands on `done` with the right quantum.

---

## 3. Local dev posture

For every feature in this plan:

1. **Default to offline.** Excel export, Word export, evidence
   checklist, sub-scores, and the legal corpus all work with zero
   network calls.
2. **Settings flags for any external dependency.** SES, EUR-Lex,
   BAILII each have a `_LIVE` flag in `settings.py` that defaults to
   `0`. Tests assert the offline path; integration tests behind
   `RUN_LIVE=1`.
3. **Demo voyage stays green.** The Rotterdam fixture is the smoke
   test for every wave. Anything that breaks the EUR 84,375.00 gate
   is a P0.
4. **Playwright golden path** (introduced in Tier 2 CI work): upload
   the three demo PDFs, watch the pipeline finish, click "Download
   PDF", click "Download Word", click "Email letter" (mocked SES).
   Locks the four claim-export paths.

---

## 4. Production readiness checklist before any deploy

Each feature in this plan is held to this checklist before its merge
to `main` triggers a deploy:

- [ ] Schema additions announced 24 hours ahead, mirrored in both
      `schemas.py` and `lib/types.ts` (or feature-local models if
      the schema is frozen and the addition is local-scope).
- [ ] Money never the model's. Deterministic Python re-derivation
      for every monetary or boolean field.
- [ ] Citation never the model's: `verified_via_tool=True` enforced
      at the schema layer.
- [ ] Tests: schema round-trip, deterministic helper unit test,
      snapshot test against the Rotterdam fixture, Playwright golden
      path stays green.
- [ ] Egress audited: every new outbound call (SES, EUR-Lex, BAILII)
      goes through `outbound.py` with logging + rate limit + cache.
- [ ] Audit row written for every state mutation.
- [ ] Feature flag wired so the change can land cold and be flipped
      on per workspace.
- [ ] Docs: a one-page note under `notes/` per feature, even if it
      is just the schema comment and the test path. Future-us thanks
      present-us.

---

## 5. Quick answers to the founder's questions

1. **"Do you need any documentation to do this, e.g. Word or Google
   Docs?"** No third-party documentation beyond what we already use.
   Word goes client-side via the `docx` npm package; we own it. Google
   Docs is out of scope.

2. **"Should we give agents tools to cite Greek or EU law precedence?"**
   Yes, and the design is in section 1.6. The architecture builds the
   tool surface once and reuses it for the compliance product (Pick 1
   in [product_roadmap.md](product_roadmap.md)).

3. **"Is there a way to download English / Greek / EU maritime laws
   for the agents to cite?"**
   - **EU**: yes, free, at scale. EUR-Lex CELLAR REST API gives full
     directive / regulation / CJEU case texts. Use as a tool.
   - **UK**: mostly yes via BAILII; full Lloyd's Reports text is
     paywalled (i-law.com), so we work from headnotes for the cases
     in the corpus and link to BAILII for full text where available.
   - **International / IMO**: yes for the conventions themselves
     (public domain), no for IMO Vega database (subscription).
     Commit the convention texts.
   - **Greek**: limited. The Government Gazette has no API; the Code
     of Private Maritime Law (KIND) text is available via several
     legal publishers (subscription) or the official codex. Manual
     curation into the JSONL is the right v0.1 answer.

   In short: most of what we want is free or curatable; the bottleneck
   is the curation, not the access. Treat the corpus as a small,
   high-quality dataset that grows quarterly, not as a giant index we
   try to scrape end-to-end.

---

## 6. Owners

- **Backend (everything in section 1.1, 1.3, 1.4, 1.5, 1.6, 2.1,
  2.2, 2.3):** dkall.
- **Frontend (1.2 Word button, 1.4 Evidence tab, 1.5 sub-score panel,
  2.1 invitations + settings UI):** Roman.
- **Infrastructure (SES setup, S3 inbound bucket, Lambda for ingest,
  Cognito wiring for the invitation flow):** Panos.

Each subphase one PR off `main`. The plan itself lives on its own
branch; this is documentation work.
