# Product roadmap — completing demurrage, then two new AI services

> Everything that is NOT covered by the Tier 0 deploy plan or the six
> follow-on items in the prior thread. This is the thorough plan for
> "what makes Laytimely a complete product, not a demurrage demo."
>
> Two halves: finish the demurrage offering so it stands up against the
> incumbents (sections 1-3), then add two adjacent AI services that
> reuse the same pipeline and give us a multi-product platform shape
> (section 4). Sequencing in section 5; risks in section 6.

---

## 0. Gap analysis: what `notes/` already covers, what it does not

Skimmed every doc under `notes/` before writing this. The current
coverage and the gaps:

**Already specified (do not duplicate):**

- Hackathon MVP and its four agents: [00-PLAN.md](00-PLAN.md),
  [03-agents.md](03-agents.md), [04-schemas.md](04-schemas.md),
  [11-prompts.md](11-prompts.md).
- Production deploy briefs: [18-production-platform-dkall.md](18-production-platform-dkall.md),
  [19-production-reasoning-panos.md](19-production-reasoning-panos.md),
  [20-production-frontend-roman.md](20-production-frontend-roman.md).
- Tier 0 deploy: [22-tier-0-deploy-plan.md](22-tier-0-deploy-plan.md),
  [first_customer_checklist.md](first_customer_checklist.md).
- The auth stub and its Cognito swap: [21-authentication-stub.md](21-authentication-stub.md).
- Three near-term features: [new_features/01-edit-with-ai.md](new_features/01-edit-with-ai.md),
  [02-research-agents.md](new_features/02-research-agents.md),
  [03-both-sides-defense.md](new_features/03-both-sides-defense.md).
- Frontend revamp + landing page: [frontend_revamp_plan.md](frontend_revamp_plan.md),
  [landing_page_plan.md](landing_page_plan.md).

**Not specified anywhere (this doc covers):**

- Live exposure detection (proactive monitoring before a claim
  crystallizes).
- Claim strength scoring beyond a single word label.
- Email-in document ingestion at scale.
- Multi-tenant workspaces and roles.
- Audit logging.
- A public API and webhooks (the "API Solutions" pillar shipping
  buyers expect).
- Notifications (time bar, exposure, settlement).
- Billing.
- Reporting and multi-voyage analytics.
- Two new product lines beyond demurrage (sections 4.1 and 4.2).

---

## 1. The complete demurrage product

The user named four items as the test for a complete demurrage offering.
Status of each against the codebase as of `docs/first-customer-checklist`:

### 1.1 Auto laytime reconstruction (DONE)

Agent 1 extracts SoF events from PDFs; Agent 2 classifies each event
(LLM) and sums hours in deterministic Python. The Rotterdam fixture is
locked at EUR 84,375.00 by `tests/test_calculator.py`. The pipeline
already supports owner / charterer perspectives.

**What is left to be considered complete:**

- Multi-port voyages (currently single port). Schema change to
  `StatementOfFacts` to carry an ordered list of port calls.
- Time charters (NYPE 93 form) in addition to voyage charters
  (ASBATANKVOY, GENCON). A new `CharterParty.form` value plus an
  alternative extractor prompt.
- Noisy or scanned SoFs. Today the pipeline fails loudly when
  pdfplumber returns no text. Add a Claude `document` block fallback
  for image-only PDFs, gated by a settings flag so the loud failure
  stays default.

### 1.2 One-click claim pack generation (DONE)

Agent 4 produces a `ClaimPacket` with the BIMCO letter, dispute
narrative, supporting documents list, and time-bar metadata. The
frontend exports it to PDF client-side.

**What is left to be considered complete:**

- Excel laytime export (Panos P8 from the production briefs). The
  spreadsheet is what 80% of shipping ops teams want for their own
  records.
- Word `.docx` export client-side. Lawyers redline in Word.
- Email send for the finished claim packet via SES (Panos P7).
- An explicit "Evidence checklist" panel in the packet: list every
  supporting document the recipient should receive, flag any that are
  not yet attached. This makes the pack ship-ready, not draft-ready.

### 1.3 Claim strength scoring (PARTIAL)

`DisputeAnalysis.flagged_events[].owner_position_strength` is a float
the model emits; the UI surfaces it as a word (Strong, Arguable, Weak).

**What is left to be considered complete:**

- Extend `FlaggedEvent` with named sub-scores (announce the frozen
  schema break first, per the working rules):
  - `clause_clarity`: how unambiguously the CP clause supports our
    position.
  - `evidence_completeness`: do we have every document the argument
    needs.
  - `counterparty_pushback_risk`: predicted likelihood the charterer
    rejects, based on the precedent in the analyst's prompt.
  - `time_bar_risk`: derived from days_until_time_bar.
- Calibrate the agent against a small labelled dataset (50-100 past
  claims labelled with outcome). Until that exists, ship the four
  sub-scores as Strong / Arguable / Weak words.
- Surface the sub-scores in the case detail right rail under
  Calculation, not as a number on screen.

### 1.4 Live exposure detection (NOT BUILT)

Today we recover claims AFTER laytime is blown. Live exposure detection
is the preventative complement: monitor voyages in flight and tell the
owner "you are 8 hours into a 12-hour weather stoppage at Rotterdam; if
it slips past 18:00 you lose EUR 12,500 of laytime allowance."

This is the biggest gap and the most differentiated feature. Designed
in detail in [section 4.2](#42-pick-2--live-exposure-detection-claims-radar)
because it doubles as one of the two new product lines.

---

## 2. Infrastructure and platform work

Ordered by impact. Everything in this section is post-Tier-0 and
pre-Series-A.

### 2.1 Email-in ingestion (high value, low cost)

A unique inbox address per workspace. SoFs, CPs, NORs, demurrage
correspondence land as email attachments. The system parses the email,
matches it to an existing voyage or opens a new one, and surfaces it.
Removes the manual "drag and drop" step that gates daily use.

- Files: `apps/api/portside_api/ingest/email.py`,
  `apps/api/portside_api/routes/inbox.py`.
- Stack: AWS SES inbound rule writes to S3; a Lambda fires on
  PutObject and POSTs to `/voyages/from-email`; the backend parses the
  MIME and runs the pipeline.
- Security: SPF / DKIM / DMARC enforced at SES, attachments scanned
  via ClamAV in Lambda, 25 MB cap per message.

### 2.2 Multi-tenant workspaces

The auth stub today is a single user. Real teams need members, roles
(owner, admin, member, viewer), workspace-scoped voyages, invitations.

- Schema additions: `workspaces`, `memberships`, `invitations` tables;
  every existing `Voyage.user_id` becomes `workspace_id`. This breaks
  the frozen schema; announce, mirror, and migrate in one PR.
- Feature-flagged so the default "single user" path keeps working
  until enabled per workspace.

### 2.3 Audit log

Every voyage create, voyage delete, revise apply, claim send. Required
for compliance and customer trust. Append-only.

- Files: `apps/api/portside_api/audit.py`.
- Stack: a dedicated `audit_events` table plus a CloudWatch sink for
  the long tail. Surface in-product on a Settings → Audit page for
  workspace admins.

### 2.4 Notifications

- Time-bar countdown alerts (90-day contractual deadline).
- Exposure alerts (when 2.5 below flags risk).
- Settlement-state changes for downstream automations.
- Channels: email via SES; in-app banner; optional SMS via SNS on
  Enterprise.

### 2.5 Public API + webhooks (the "API Solutions" pillar)

Shipping companies have TMS systems (Veson IMOS, ShipNet, Dataloy);
they want to push voyage docs in and pull claim packets out via API
rather than a UI. Webhooks for stage transitions and time-bar warnings.

- Files: `apps/api/portside_api/public_api/` (a thin re-export of the
  internal routes with API-key auth instead of cookies).
- OpenAPI 3.1 spec generated from the FastAPI app, hosted at
  `https://laytimely.com/api/v1/openapi.json`.
- API key issuance flow on a Settings → API keys page.

### 2.6 Billing

Stripe Checkout for self-serve plans, manual invoicing for partner /
enterprise tiers. Pricing options:

- Self-serve subscription: EUR 199/month for one workspace, unlimited
  voyages.
- Per-recovery fee: 5% of recovered amount, billed monthly.
- Enterprise: custom, includes SSO, audit log, dedicated CSM.

Webhook handler on Stripe events, usage metering against voyage
count, dunning emails for failed cards.

### 2.7 Observability hardening (Tier 2)

- Sentry release tagging + source maps on both apps.
- CloudWatch 5xx + p95 latency alarms to ops email.
- Structured JSON logging with actor + voyage_id on every log line.
- P9 full: rate limiting on /login + /voyages, error taxonomy
  (4xx vs 5xx classification), pipeline timeout / retry audit.

### 2.8 Mobile companion (deferred to year 2)

A read-only iOS / Android app for claims executives in transit. Shows
the queue, latest letters, accept / reject revises. React Native.
Not on the critical path; record for completeness.

---

## 3. Demurrage completeness rollup

Mapping the four items the user named to the sections above:

| User item | Status | Where it lands |
| --- | --- | --- |
| Live exposure detection | NOT BUILT | section 4.2 (also a new product line) |
| Auto laytime reconstruction | DONE for v0.1 | section 1.1 polish: multi-port + time charter + OCR fallback |
| Claim strength scoring | PARTIAL | section 1.3 sub-scores + dataset |
| One-click claim pack generation | DONE for v0.1 | section 1.2 polish: Excel + Word + email + evidence checklist |

Two items done, two items partial-to-not-done. The two left are the
single biggest reasons the product feels "demo" today rather than
"complete." Both ship in the first six weeks after Tier 0 lands.

---

## 4. Two new AI services to ship next

From the twelve services the user listed:

- Real-time monitoring · Route optimisation · Emissions analysis · EU
  allowances management · EU ETS compliance · FuelEU maritime
  compliance · API solutions · Speed claim consultancy · Post-voyage
  analysis · Yachting & cruising · Oil and gas commodity traders ·
  Weather routing.

Picked the two with the highest **regulatory urgency + reuses our
pipeline + non-saturated market** score. The other ten are addressed
in [section 4.3](#43-rejected-and-why).

### 4.1 Pick 1 — EU ETS + FuelEU Maritime compliance (bundled)

**Why now.** As of 1 January 2024 (EU ETS extension to shipping) and 1
January 2025 (FuelEU Maritime), ship owners trading in EU waters MUST
report fuel consumption, carbon emissions, and energy intensity.
Non-compliance attracts fines up to EUR 100 per excess tonne of CO2
plus possible operational bans. The market is greenfield: every
shipping company we would sell to is scrambling for a tool right now.
Willingness to pay is high because the alternative is a fine.

**Why us.** Compliance is a calculation problem driven by voyage data.
Same shape as laytime: extract from documents, classify events, compute
deterministically, generate a report. The voyage state we already
build (extraction + laytime) carries ~60% of the inputs: port pairs,
voyage duration, vessel particulars. We bolt on Bunker Delivery Notes
(BDN) and a fuel/speed curve, and the math falls out the back.

**What it would look like.**

- New `EmissionsAgent` agent. Inputs: the existing `ExtractionResult`,
  uploaded BDNs, AIS distance for the EU-fraction of the voyage, the
  vessel's fuel/speed curve (uploaded once per vessel). Output:
  `VoyageEmissionsReport` (new schema):
  - Total CO2e by scope and gas (CO2, CH4, N2O).
  - EU ETS allowances due (EUAs for the EU-fraction).
  - FuelEU intensity in gCO2e/MJ vs the 2025 target line.
  - Pooling and banking eligibility flags.
- New surfaces `/emissions` (workspace rollup) and
  `/emissions/<voyage_id>` (per-voyage), styled with the same eyebrow +
  hero pattern as the case detail.
- Annual rollup report (Excel + PDF), the artifact the regulator and
  the auditor want.

**Build cost.** ~3-4 weeks for v0.1 against synthetic data; another
4-6 weeks to land a paying design partner. Reuses `agents/llm.py`, the
prompt cache, the structured-output discipline, the PDF export. Only
genuinely new infrastructure is the vessel-particulars and fuel-curve
schema plus the BDN parser (similar shape to the SoF parser).

**Pricing wedge.** EUR 50-100 per voyage report. EUR 5-15k/year for the
annual rollup. Industry buys software per-vessel; line items exist in
every ops budget for compliance tooling.

### 4.2 Pick 2 — Live Exposure Detection (Claims Radar)

**Why now.** Completes the demurrage offering per the user's first
item. Today we recover claims AFTER laytime is blown; with live
monitoring we tell the customer "vessel V is N hours into an M-hour
weather stoppage at port P; if it slips past T you lose EUR X of
laytime allowance" BEFORE the claim crystallizes. Doubles our
footprint per customer: now we sell prevention AND recovery.

**Why us.** It is a streaming agent on top of the same voyage state.
The reasoning over inputs is exactly what our four-agent pipeline
already does for closed voyages; we are reusing 80% of the codebase.
The hard part is data sourcing.

**What it would look like.**

- New `monitor` agent that runs on a 15-minute schedule per active
  voyage. Inputs:
  - AIS position via MarineTraffic or Spire (paid API, ~EUR 0.50 per
    vessel-day at our scale).
  - Berth status via the port authority public feed for the busiest
    ports (Rotterdam, Singapore, Hamburg, Antwerp).
  - Weather at the discharge port via Open-Meteo (already wired in
    [new_features/02-research-agents.md](new_features/02-research-agents.md)).
  - Email-in (section 2.1) for forwarded operator updates.
- Output schema extends `FlaggedEvent` with a `predicted: bool` flag;
  predicted events are not yet in the SoF but the agent thinks they
  will be.
- Surfaces:
  - A new `/monitor` dashboard listing every active voyage and its
    exposure status, sorted by predicted-loss desc.
  - Per-voyage timeline of triggers and projected loss.
  - Alerts via email (section 2.4) when a configurable threshold is
    crossed.
- Settings: per-workspace threshold (EUR loss, hours of delay) for
  when to alert vs when to surface silently.

**Build cost.** ~5-7 weeks. The AIS, weather, and port-feed
integrations are the long pole; the agent reasoning is short. Plan to
ship one integration per week and gate the product on AIS alone
behind a feature flag if the other two slip.

**Pricing wedge.** EUR 200-500 per vessel per month, scaled by alerts
acted on. This is the first recurring-revenue line on top of the
per-claim fees the demurrage product earns. Strategic value: it is the
hook that justifies the long-term contract.

### 4.3 Rejected, and why

- **Route optimization / weather routing**: capital-intensive
  (training routing models on AIS data is millions of vessel-days),
  saturated (StormGeo, Bearing AI, Marorka, OrbitMI). We have no edge
  here.
- **EU Allowances trading**: requires a regulatory licence to act as
  broker. Outside our scope and our risk appetite. We help calculate
  the allowances due (Pick 1); the actual trade we hand off.
- **Yachting & cruising**: different document flows (CPs do not
  apply), different buyer (charter management companies, not owners),
  different scale (sub-100 voyages per year).
- **Speed claim consultancy**: small market; speed claims are mostly
  handled in-house at major owners. Revisit as a section of the
  laytime product, not as a standalone.
- **Oil and gas commodity traders**: a customer segment, not a
  product. They buy our demurrage and compliance products like
  everyone else.
- **Post-voyage analysis**: useful dashboard add-on, but not a
  standalone willingness-to-pay. Bundle into the multi-voyage
  analytics in section 2 once we have ten paying customers.
- **API solutions**: this IS in the plan (section 2.5), but as
  infrastructure rather than a separate product line. Selling APIs as
  a primary line of business needs at least one other live product
  first.
- **Real-time monitoring as the category name**: this is exactly what
  Pick 2 is, framed under our own brand (Claims Radar). The category
  is too broad to be a product; the application to laytime is the
  product.

---

## 5. Sequencing — the next 12 weeks

| Weeks | Theme | Concrete output |
| --- | --- | --- |
| 1-2 | Tier 0 deploy goes live (already specced in [22-tier-0-deploy-plan.md](22-tier-0-deploy-plan.md)) | papership-web.vercel.app → laytimely.com, App Runner backend live |
| 3-4 | Backend rename `portside_api` → `laytimely_api`; Cognito + RDS + S3 provisioned; frontend auth swap merged; Sentry minimum | Real users on Cognito sessions, error visibility on both apps |
| 5-6 | Demurrage completeness wave 1: Excel + Word + email send for claim pack, evidence checklist panel, claim strength sub-scores | Customer-visible polish; tests for each export format |
| 7-8 | Platform wave 1: multi-tenant workspaces, audit log, email-in ingestion | First customer onboarded with their own team; SoFs arriving by email |
| 9-11 | Pick 1: EU ETS + FuelEU compliance v0.1 | Working /emissions surface, EmissionsAgent, an annual rollup PDF; one paying design partner |
| 12+ | Pick 2: Live Exposure Detection v0.1 | /monitor dashboard against one AIS provider, weather, two port feeds; one design partner running it on three vessels |

Demurrage completeness items (section 1) fold into weeks 5-8. The two
new product lines (section 4) own weeks 9-12+. The platform work
(section 2) is interleaved so it is not a separate quarter.

---

## 6. Risk register

| Risk | Mitigation |
| --- | --- |
| Compliance product is regulation-driven: every delay in EU rulemaking is a delay in buyer urgency | Ship v0.1 against published 2025 rules; iterate behind feature flags. |
| AIS and port-feed integrations are paid and rate-limited | Start with Open-Meteo (free) plus one paid AIS source; cap voyages-per-customer in early pricing tiers. |
| Email-in security: we ingest arbitrary attachments from outside | SES inbound with SPF/DKIM/DMARC enforced, ClamAV scan in Lambda, 25 MB cap per message, drop anything that fails. |
| Multi-tenant migration breaks the single-user happy path | Feature flag the workspaces concept; default-to-personal-workspace until enabled per account. |
| The two new products dilute focus from the demurrage core | Both extend the demurrage pipeline: same agents, same orchestrator, same schemas with additive fields. Neither needs a separate codebase. |
| Pricing the live monitoring product wrong (too cheap, customers under-use it; too expensive, no adoption) | Launch at EUR 299/vessel/month flat; iterate after the first three customers. The recurring shape matters more than the exact number. |
| Pick 1 (compliance) gets commoditised by a bigger player | We have ~12-18 months before Veson or DNV ships a credible competitor. Lock in design partners by month 6. |
| The frontend revamp introduces a regression we miss because we have no E2E tests | Add Playwright golden path (upload → done → letter) as part of the Tier 2 CI work. |

---

## 7. What is NOT in this plan

Recording for completeness so we do not relitigate them this quarter:

- A mobile app (year 2).
- A real-time vessel tracking dashboard at the resolution incumbents
  offer (saturated, capital-intensive, not our edge).
- Cargo damage claims (similar shape to demurrage; revisit after
  compliance lands).
- General Average claims (rare, very lucrative, very specialised;
  revisit at first customer request).
- A CMS for the marketing site (premature).
- A community / forum (premature, not our value).
- Crypto / web3 / NFT anything. The answer will come up; the answer
  is no.

---

## 8. Owner and timing

- Engineering: dkall + Panos + Roman, split as today (backend agents
  and platform / deploy and ops / frontend).
- Product and sales: founder calls until first five paying customers.
- Branch policy: each subphase one PR off `main`; the plan itself
  lives on `docs/first-customer-checklist` because it is documentation
  work.
- Twelve weeks from Tier 0 going live to: a complete demurrage
  product, a working EU ETS / FuelEU compliance offering with a paying
  design partner, and live exposure detection running on three
  vessels for a second design partner.
