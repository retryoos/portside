# Laytimely — Roadmap

> **Bucket 2 of 3. This is the single source of truth for planned, not-yet-built
> work.** Anything already shipped lives in [SYSTEM.md](SYSTEM.md); how to run
> and ship lives in [OPERATIONS.md](OPERATIONS.md). See [README.md](README.md)
> for the scoping rule.
>
> This file is the **overview and prioritisation**. Two future product lines
> have full design depth in their own bucket-2 docs, which this file points to
> rather than duplicates:
> [architecture_claims_radar.md](architecture_claims_radar.md) and
> [architecture_emissions_compliance.md](architecture_emissions_compliance.md).
>
> Last consolidated: 2026-05-31. Convert relative dates to absolute when adding
> items.

---

## 0. What is already done (do not re-plan)

The hackathon MVP, the Laytimely rebrand, the R0-R8 frontend revamp, and the
entire "weeks 5-8" build all shipped. That means these are **done** and
documented in [SYSTEM.md](SYSTEM.md), not here:

- Four-agent pipeline, deterministic laytime arithmetic, inline revision.
- Excel + Word + PDF export; SES claim-letter email send.
- Evidence checklist; claim-strength sub-scores.
- Legal citation subsystem with verified authorities.
- Multi-tenant workspaces + roles + invitations; audit log; email-in ingestion.
- Postgres-ready SQLAlchemy persistence; S3-ready object storage; JWT auth stub.
- Research agent; both-sides (charterer) defense.

The roadmap below is only what remains.

---

## 1. Complete the demurrage product

| Item | Status | Work remaining |
| --- | --- | --- |
| Auto laytime reconstruction | shipped for single-port voyage charter | multi-port voyages (ordered port-call list on `StatementOfFacts`); time charters (NYPE 93 form + alt extractor prompt); OCR fallback for scanned/image-only SoFs (Claude `document` block, gated by a flag so loud-failure stays default) |
| Claim strength scoring | sub-scores shipped as words | calibrate against a labelled dataset of 50-100 past claims with outcomes, then graduate from words to a calibrated score |
| **Live exposure detection** | **not built** | the biggest gap; full design in [architecture_claims_radar.md](architecture_claims_radar.md). See §3.1 |

---

## 2. Platform and infrastructure (post-Tier-0, pre-Series-A)

Ordered by impact. Workspaces, audit log, and email-in are **already shipped**
(see SYSTEM.md); what remains:

- **Notifications (§2.4 of the old roadmap).** Time-bar countdown alerts,
  exposure alerts (depends on §3.1), settlement-state changes. Channels: SES
  email, in-app banner, optional SMS via SNS on Enterprise.
- **Public API + webhooks ("API Solutions" pillar).** Shipping TMS systems
  (Veson IMOS, ShipNet, Dataloy) want to push docs in and pull claim packets
  out. A thin `public_api/` re-export of internal routes with API-key auth, an
  OpenAPI 3.1 spec at `laytimely.com/api/v1/openapi.json`, an API-keys settings
  page, and webhooks for stage transitions + time-bar warnings.
- **Billing.** Stripe Checkout for self-serve; manual invoicing for enterprise.
  Candidate pricing: EUR 199/mo per workspace (unlimited voyages), or 5% of
  recovered amount, or enterprise custom (SSO, audit log, CSM). Usage metering
  on voyage count, dunning on failed cards.
- **Observability hardening (Tier 2).** Sentry release tagging + source maps on
  both apps; CloudWatch 5xx + p95 alarms to ops; structured JSON logging with
  actor + voyage_id; rate limiting on `/login`; error taxonomy; pipeline
  timeout/retry audit. (See [OPERATIONS.md](OPERATIONS.md) for the deploy-side
  hardening checklist.)
- **Reporting / multi-voyage analytics.** Bundle "post-voyage analysis" here
  once there are ~10 paying customers; not a standalone product.
- **Mobile companion (year 2).** Read-only iOS/Android queue + letters +
  accept/reject revises. React Native. Off the critical path.

---

## 3. Two new AI services (the multi-product platform shape)

Both extend the existing pipeline (same agents, orchestrator, additive schema
fields), so neither needs a separate codebase. Picked from twelve candidate
services for highest regulatory urgency + pipeline reuse + non-saturated market.

### 3.1 Claims Radar — live exposure detection

Monitor voyages in flight and warn before a claim crystallises ("vessel V is N
hours into an M-hour weather stoppage at port P; if it slips past T you lose
EUR X of laytime allowance"). Sells prevention alongside recovery; first
recurring-revenue line (EUR 200-500 / vessel / month).

- A `monitor` agent on a 15-minute schedule per active voyage; inputs are AIS
  (MarineTraffic/Spire), berth status (port public feeds), weather (Open-Meteo,
  already wired via the research agent), and email-in operator updates.
- Extends `FlaggedEvent` with a `predicted: bool` flag; a `/monitor` dashboard
  sorted by predicted loss; threshold-based alerts.
- **Cost:** ~5-7 weeks; AIS/port-feed integrations are the long pole. Gate on
  AIS alone behind a flag if the others slip.
- **Full design:** [architecture_claims_radar.md](architecture_claims_radar.md).

### 3.2 EU ETS + FuelEU Maritime compliance (bundled)

Owners trading in EU waters must report fuel/emissions/energy-intensity since EU
ETS shipping extension (Jan 2024) and FuelEU Maritime (Jan 2025); non-compliance
draws fines (up to EUR 100/excess-tonne CO2) and operational bans. Greenfield
market, high willingness to pay.

- A new `EmissionsAgent`; inputs are the existing `ExtractionResult` plus Bunker
  Delivery Notes, AIS distance for the EU-fraction, and a per-vessel fuel/speed
  curve. Output `VoyageEmissionsReport`: CO2e by scope/gas, EU ETS allowances
  due, FuelEU intensity vs target, pooling/banking flags.
- New `/emissions` (workspace rollup) and `/emissions/<voyage_id>` surfaces;
  annual rollup report (Excel + PDF).
- **Cost:** ~3-4 weeks for v0.1 vs synthetic data; +4-6 weeks to a paying design
  partner. New work is the vessel/fuel-curve schema + BDN parser.
- **Pricing:** EUR 50-100 per voyage report; EUR 5-15k/year for the rollup.
- **Full design:** [architecture_emissions_compliance.md](architecture_emissions_compliance.md).

### 3.3 Rejected services (recorded so we do not relitigate)

Route optimisation / weather routing (capital-intensive, saturated); EU
allowance trading (needs a broker licence; we calculate, we do not trade);
yachting & cruising (different doc flows and buyers); speed-claim consultancy
(small market, mostly in-house); oil & gas traders (a segment, not a product);
post-voyage analysis (an analytics add-on, not standalone); API solutions
(infrastructure per §2, not a primary line yet). Crypto/web3/NFT: no.

---

## 4. Indicative sequencing (12 weeks from Tier 0 live)

| Weeks | Theme |
| --- | --- |
| 1-2 | Tier 0 demo live (see OPERATIONS.md): Vercel frontend + off-AWS backend, `laytimely.com` attached |
| 3-4 | First paying customer: AWS migration (Cognito + RDS + S3 + Fargate), Sentry minimum (see OPERATIONS.md) |
| 5-6 | Demurrage completeness: multi-port, time charters, OCR fallback, strength calibration dataset |
| 7-8 | Platform: notifications, public API + webhooks, billing |
| 9-11 | Claims Radar v0.1 (one AIS provider + weather + two port feeds) |
| 12+ | EU ETS / FuelEU compliance v0.1 (one paying design partner) |

(The weeks-5-8 features in earlier plans already shipped; this sequence is the
remaining work, re-based on the current state.)

---

## 5. Explicitly out of scope this quarter

Mobile app (year 2); incumbent-resolution vessel tracking; cargo-damage claims
(revisit after compliance); General Average (rare/specialised, on request); a
marketing CMS; a community/forum; crypto/web3.

---

## 6. Risk register

| Risk | Mitigation |
| --- | --- |
| Compliance product is regulation-paced | Ship v0.1 against published 2025 rules; iterate behind flags |
| AIS / port feeds are paid + rate-limited | Start free (Open-Meteo) + one paid AIS; cap voyages-per-customer in early tiers |
| Two new products dilute the demurrage core | Both reuse the pipeline; additive schema fields only |
| Mispricing live monitoring | Launch flat (~EUR 299/vessel/mo); iterate after three customers |
| Compliance gets commoditised by Veson/DNV | ~12-18 month window; lock design partners by month 6 |
| Frontend revamp regressions | Add a Playwright golden-path E2E (upload -> done -> letter) in Tier 2 CI |
