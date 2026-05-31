# Architecture — EU ETS + FuelEU Maritime compliance (Pick 1)

> Production-grade specification for the second product line. Builds on the
> same four-agent pipeline + legal subsystem the demurrage workflow uses, so
> the next engineer can implement end-to-end without rediscovering the
> regulatory rules from scratch.
>
> Pitch and rejection set are in [product_roadmap.md §4.1](product_roadmap.md).
> This document is the build spec.

---

## 0. Why this is a calculation problem, not a model problem

EU ETS Maritime and FuelEU Maritime are both **regulator-defined formulas**
over a small set of voyage inputs. The model's job is to extract the inputs
(from Bunker Delivery Notes, the existing extraction tree, and a once-per-
vessel particulars sheet); every euro figure and every gCO2e/MJ number is
deterministic Python that an accredited verifier (DNV, Lloyd's Register,
ClassNK, etc.) can re-derive line by line.

This is the same posture as laytime: model extracts, code computes, output
cites the source for every number. The architecture below is built around
that posture.

---

## 1. Regulatory primer (just enough)

Both regimes apply to commercial vessels ≥ 5,000 GT carrying cargo or
passengers in the EU/EEA.

### 1.1 EU ETS Maritime — Directive 2003/87/EC as amended by 2023/959

- **Scope:** CO2 emissions on voyages that touch an EU/EEA port. Intra-EU
  voyages count 100% of CO2; voyages with one EU leg count 50%.
- **Phase-in:** 40% of allowances surrendered for 2024 emissions, 70% for
  2025, **100% from 2026** onwards.
- **Methane and nitrous oxide:** from 1 January 2026 onwards, CO2-equivalent
  CH4 and N2O are included alongside CO2.
- **Reporting:** the existing MRV regime (Regulation (EU) 2015/757) is the
  data backbone. Verifier issues a Verification Statement; the shipping
  company surrenders EUAs by 30 September of the following year.
- **Penalty for non-compliance:** EUR 100 per excess tonne CO2 (with annual
  inflation indexation) + possible operational ban.

### 1.2 FuelEU Maritime — Regulation (EU) 2023/1805

- **Scope:** annual GHG intensity (gCO2e/MJ) of the energy used on board,
  measured well-to-wake (WtW). Covers CO2, CH4, N2O.
- **Targets, vs the 2020 reference intensity of 91.16 gCO2e/MJ:**
  - 2025: −2%
  - 2030: −6%
  - 2035: −14.5%
  - 2040: −31%
  - 2045: −62%
  - 2050: −80%
- **Pooling:** ships can pool to a fleet-average intensity; over-compliers
  can sell credits to under-compliers.
- **Banking + borrowing:** carry compliance surplus forward; borrow against
  future years up to 2%.
- **Penalty:** EUR 2,400 per tonne VLSFO-equivalent of the gap × intensity
  shortfall × energy used.

### 1.3 What we promise the verifier

- Every tonne of fuel: type, mass, lower heating value (LHV), emission
  factor (well-to-tank + tank-to-wake), source document (BDN), date.
- Every nautical mile: AIS source, segment start/end, EU/EEA fraction
  factor.
- Every formula: cited to the article it implements.
- Every number that ends up on the surrendered-allowances line is
  re-derivable from the inputs.

---

## 2. Goals + non-goals

### Goals (v0.1 → v1.0)

- Produce per-voyage emissions reports (EUAs due, FuelEU intensity, gap).
- Produce annual rollups in the format a verifier will accept (PDF + Excel +
  source-data export).
- Cite the regulation by article, every time.
- Run offline by default against a committed reference factor table.
- Stay aligned with the legal citation subsystem (§1.6) so a "Why this
  number?" link surfaces the exact regulation text.

### Non-goals

- We do **not** act as a verifier. We produce the workbook a verifier
  approves.
- We do **not** trade EUAs. We compute the quantity due; the customer or
  their broker buys and surrenders.
- No AIS-derived bunker estimation in v0.1. The customer supplies the BDNs;
  AIS is used only for distance and EU-fraction.
- No SECA (Sulphur Emission Control Area) reporting. Different regulator,
  different forms, future work.

---

## 3. The data model

Two new feature-local Pydantic modules + three new SQL tables. The frozen
`schemas.py` is **not** touched.

### 3.1 New tables

```
vessels (
    id PK,                     -- workspace-scoped vessel slug
    workspace_id FK,
    imo_number VARCHAR(7) UNIQUE,
    name, flag, type,
    gross_tonnage INTEGER,
    deadweight_tonnage INTEGER,
    main_engine_power_kw FLOAT,
    auxiliary_engine_power_kw FLOAT,
    fuel_speed_curve JSONB,    -- [{kn, t_per_day}, ...] piecewise linear
    created_at, updated_at
)

bunker_delivery_notes (
    id PK,
    vessel_id FK,
    voyage_id FK NULLABLE,     -- nullable: BDN can predate a voyage
    fuel_type VARCHAR,         -- one of the closed fuel-type Literal below
    quantity_mt FLOAT,
    delivery_port VARCHAR,
    delivered_at TIMESTAMP,
    source_object_key VARCHAR, -- S3 key of the uploaded PDF
    extracted_at TIMESTAMP,
    raw_extraction JSONB,      -- audit trail of the AGENT extraction
    redacted BOOLEAN DEFAULT FALSE
)

voyage_emissions_reports (
    id PK,
    voyage_id FK UNIQUE,
    workspace_id FK,
    year INTEGER,              -- the regulatory year of the report
    eu_fraction FLOAT,
    co2_tonnes_total FLOAT,
    co2_tonnes_eu FLOAT,
    co2e_tonnes_total FLOAT,   -- includes CH4 + N2O from 2026 onwards
    co2e_tonnes_eu FLOAT,
    energy_mj_total FLOAT,
    fueleu_intensity FLOAT,    -- gCO2e/MJ
    fueleu_target FLOAT,       -- gCO2e/MJ for `year`
    fueleu_gap FLOAT,          -- target - actual (positive = compliant)
    eu_ets_phase_in_factor FLOAT,
    eu_ets_allowances_due FLOAT,
    eu_ets_allowances_due_cost_eur FLOAT,
    fueleu_penalty_eur_at_gap FLOAT,
    computed_at TIMESTAMP,
    inputs_snapshot JSONB,     -- the full ComputeInputs that produced this row
    citations JSONB            -- list[CitedAuthority] for the verifier
)
```

Alembic migration adds these as a single PR, since they only depend on each
other and on the existing `workspaces` table (§2.1).

### 3.2 Fuel type vocabulary (closed)

```python
FuelType = Literal[
    "HFO",       # Heavy Fuel Oil
    "VLSFO",     # Very Low Sulphur Fuel Oil
    "MGO",       # Marine Gas Oil
    "MDO",       # Marine Diesel Oil
    "LNG",       # Liquefied Natural Gas
    "LPG_BUTANE",
    "LPG_PROPANE",
    "METHANOL",
    "ETHANOL",
    "BIO_MGO",   # bio diesel
    "BIO_LNG",
    "AMMONIA",   # zero TtW CO2 when blue/green
    "HYDROGEN",
    "ELECTRICITY", # cold ironing at berth
    "OTHER",     # free text; analyst flags for human review
]
```

New types added with a code change. Verifier rejects "OTHER" rows so the
helpful-but-cautious closed list is the right shape.

### 3.3 The emission-factor table (committed JSON)

```
apps/api/portside_api/emissions/factors_2024.json
apps/api/portside_api/emissions/factors_2025.json
...
```

One file per regulatory year. Each row:

```json
{
  "fuel_type": "VLSFO",
  "year": 2025,
  "lhv_mj_per_kg": 40.5,
  "co2_factor_tco2_per_t": 3.151,
  "co2_factor_tco2_per_mj": 0.0000779,
  "ch4_factor_g_per_t": 0.06,
  "n2o_factor_g_per_t": 0.16,
  "wtt_factor_gco2e_per_mj": 14.10,
  "ttw_factor_gco2e_per_mj": 77.96,
  "source": "IMO MEPC.245(66) Annex I + FuelEU Maritime Annex II"
}
```

Reference: IMO 2014 GHG Study Annex 1, Regulation (EU) 2023/1805 Annex II.
Quarterly review by the legal lead; any change is a versioned file and a
migration plus a CHANGELOG line. We freeze a year's file once
30 September of the following year passes (verifier-final).

---

## 4. The pipeline

The shape mirrors the demurrage pipeline so engineers transfer easily. Two
new agents + two deterministic helpers.

```
[ Existing extraction + bunker_delivery_notes upload + vessels registry ]
                            │
                            ▼
                    Agent E1: BDN Extractor
                  (Sonnet 4.6, strict structured)
              one BDN PDF -> BunkerDeliveryNoteRecord
                            │
                            ▼
                    Agent E2: AIS Aggregator
       Spire/MarineTraffic distance per leg -> VoyageAisLegs
       fall-back: customer-entered distance via the UI
                            │
                            ▼
              compute_emissions_voyage()  (Python)
       vessel particulars + BDNs + AIS legs + factor table
              -> VoyageEmissionsReport (numbers, no prose)
                            │
                            ▼
                    Agent E3: Verifier Narrative
                  (Sonnet 4.6, structured)
       VoyageEmissionsReport -> a short audit memo + cited authorities
       (numbers come pre-computed; model only writes prose)
                            │
                            ▼
          compute_emissions_annual_rollup(workspace_id, year)
       per-vessel + per-fuel-type aggregation -> AnnualEmissionsRollup
                            │
                            ▼
         render_verifier_workbook(rollup)  (deterministic .xlsx)
         render_verifier_letter(rollup)    (deterministic .pdf)
```

### 4.1 Agent E1 — BDN Extractor

- Input: one Bunker Delivery Note PDF (pdfplumber → text).
- Output (structured): `BunkerDeliveryNoteRecord` with `fuel_type`,
  `quantity_mt`, `delivery_port`, `delivered_at`, `lhv_mj_per_kg` (optional;
  fall back to the factor table if missing).
- Prompts: `prompts/bdn_extractor.md`. Same cross-cutting prefix as the
  rest of the agent fleet (no AI tells, clause-by-number, event-by-id).
- **Money is never the model's** stays here too: `quantity_mt` and
  `lhv_mj_per_kg` are taken as-is from the model but rejected by the route
  layer if they are outside a sane band (0 < quantity_mt ≤ 5000;
  35 ≤ lhv ≤ 50). Out-of-band values queue the BDN for human review.

### 4.2 Agent E2 — AIS Aggregator

- Input: voyage extraction (port pairs + dates), vessel IMO.
- Output: ordered list of voyage legs with start port, end port, start
  time, end time, distance NM, EU/EEA fraction (1.0 / 0.5 / 0.0 per the
  scope rule above).
- Tool: `ais_voyage_track(imo, from_ts, to_ts)` against Spire (preferred,
  ~€0.50/vessel-day) or MarineTraffic (cheaper, less granular). Wrapped via
  the same `outbound.py` egress adapter from §1.6.
- Fall-back: when AIS is not configured or for older voyages, the UI lets
  the customer enter distance per leg manually; the agent reads those rows
  instead.

### 4.3 `compute_emissions_voyage()` — deterministic Python

```python
def compute_emissions_voyage(
    *,
    vessel: Vessel,
    bdns: list[BunkerDeliveryNoteRecord],
    ais_legs: list[VoyageAisLeg],
    factor_table: dict[FuelType, EmissionFactorRow],
    regulatory_year: int,
) -> VoyageEmissionsReport:
    ...
```

Computations:

1. **Fuel consumption attribution.** Distribute each BDN across the legs
   that consumed it, proportional to the vessel's fuel/speed curve at the
   leg's average speed. Audit-friendly: every leg ends up with a
   per-fuel-type tonne split summing to the BDN total.
2. **CO2 (and CO2e from 2026).** Per leg, per fuel:
   `tCO2 = t_fuel × co2_factor_tco2_per_t`. Add CH4/N2O × GWP100 from 2026.
3. **EU fraction.** `co2_eu = Σ_legs (co2_leg × leg.eu_fraction)`.
4. **EU ETS allowances due.**
   `allowances = co2e_eu × phase_in_factor(year)`.
   Phase-in: `0.40` for 2024, `0.70` for 2025, `1.00` from 2026.
5. **FuelEU intensity.**
   `intensity = (Σ t_fuel × (wtt + ttw) factor) / energy_mj_total`
   where `energy_mj_total = Σ t_fuel × lhv_mj_per_kg × 1000`.
6. **Gap vs target.** `gap = target(year) - intensity`. Negative gap is a
   shortfall; we compute the FuelEU penalty as a *potential* exposure
   (`gap_gco2e_per_mj × energy_mj × tonnes_VLSFO_eq × 2400 EUR`).
7. **EUR price for the allowances due.** Multiply by the *current* daily
   EUA reference price from EEX or ICE; we cache the daily price in a tiny
   committed JSONL refreshed by a daily cron (or read from a settings env
   var when the cron is down).

Every step writes a line to `inputs_snapshot` so the verifier sees the
intermediate values.

### 4.4 Agent E3 — Verifier Narrative

- Input: the `VoyageEmissionsReport` (numbers already final).
- Output (structured): a short prose summary (3-5 paragraphs) that explains
  the methodology, lists the source documents, and surfaces any data-quality
  warnings the agent saw. Cited authorities required: every claim that is
  not pure arithmetic must carry a `CitedAuthority` whose
  `verified_via_tool=True` (the §1.6 verification gate is reused as-is).

### 4.5 Annual rollup

Pure Python. Per workspace per regulatory year:

- Aggregate every `VoyageEmissionsReport` for vessels owned by the
  workspace in the year.
- Apply **pooling** when the customer enrols vessels into a pool: the
  pool's intensity is the energy-weighted mean of the members.
- Apply **banking** and **borrowing**: surplus carries to the next year;
  borrow up to 2% with a 10% penalty (per Regulation 2023/1805 Article 20).
- Produce `AnnualEmissionsRollup` with: total EUAs due, total surrendered,
  shortfall (if any), FuelEU intensity vs target, gap, penalty exposure.

### 4.6 Rendering: workbook + letter

- `render_verifier_workbook(rollup) -> bytes`: an `.xlsx` (openpyxl, no
  native deps) with four sheets: Summary, Vessels (per-vessel rows),
  Voyages (per-voyage rows), Inputs (one row per BDN + one row per AIS leg).
  Snapshot-tested against a hand-worked fixture.
- `render_verifier_letter(rollup) -> bytes`: a `.pdf` (server-side via
  WeasyPrint — first place we need server-side PDF, because the verifier
  wants the PDF independent of any browser) carrying the same numbers plus
  the agent's narrative + citations.

---

## 5. Wire models (feature-local, frozen schemas.py untouched)

```python
class Vessel(BaseModel):
    id: str
    workspace_id: str
    imo_number: str = Field(..., pattern=r"^[0-9]{7}$")
    name: str
    flag: str
    type: Literal["TANKER", "BULKER", "CONTAINER", "ROPAX", "GENERAL_CARGO", "OTHER"]
    gross_tonnage: int = Field(..., ge=5000)
    deadweight_tonnage: int = Field(..., gt=0)
    main_engine_power_kw: float
    auxiliary_engine_power_kw: float
    fuel_speed_curve: list[SpeedFuelPoint]


class SpeedFuelPoint(BaseModel):
    speed_knots: float
    fuel_t_per_day: float


class BunkerDeliveryNoteRecord(BaseModel):
    vessel_id: str
    voyage_id: Optional[str]
    fuel_type: FuelType
    quantity_mt: float = Field(..., gt=0, le=5000)
    delivery_port: str
    delivered_at: datetime
    lhv_mj_per_kg: Optional[float] = Field(default=None, ge=35, le=50)
    source_object_key: str


class VoyageAisLeg(BaseModel):
    seq: int
    from_port: str
    to_port: str
    started_at: datetime
    ended_at: datetime
    distance_nm: float = Field(..., gt=0)
    eu_fraction: Literal[0.0, 0.5, 1.0]


class VoyageEmissionsReport(BaseModel):
    voyage_id: str
    workspace_id: str
    year: int
    eu_fraction: float
    co2_tonnes_total: float
    co2_tonnes_eu: float
    co2e_tonnes_total: float
    co2e_tonnes_eu: float
    energy_mj_total: float
    fueleu_intensity: float
    fueleu_target: float
    fueleu_gap: float
    eu_ets_phase_in_factor: float
    eu_ets_allowances_due: float
    eu_ets_allowances_due_cost_eur: float
    fueleu_penalty_eur_at_gap: float
    citations: list[CitedAuthority]
    inputs_snapshot: dict[str, Any]  # opaque; surfaces in the verifier xlsx
    narrative_markdown: str


class AnnualEmissionsRollup(BaseModel):
    workspace_id: str
    year: int
    vessels: list[VesselAnnualSummary]
    total_eu_ets_allowances_due: float
    total_fueleu_intensity: float
    total_fueleu_target: float
    total_fueleu_gap: float
    pooling_members: list[str]
    banking_carried_in: float
    banking_carried_out: float
    citations: list[CitedAuthority]
```

`citations` everywhere is the same `CitedAuthority` model from §1.6; the
verification gate (`verify.validate_authorities`) is reused unchanged.

---

## 6. Routes

```
POST   /vessels                          - upsert vessel particulars
GET    /vessels                          - list workspace vessels
POST   /vessels/{vessel_id}/bdn          - upload BDN PDF (multipart)
GET    /vessels/{vessel_id}/bdn          - list BDNs for the vessel

POST   /voyages/{voyage_id}/emissions    - compute (or recompute) report
GET    /voyages/{voyage_id}/emissions    - read latest report

GET    /emissions/{workspace_id}/{year}/annual         - rollup JSON
GET    /emissions/{workspace_id}/{year}/annual.xlsx    - verifier workbook
GET    /emissions/{workspace_id}/{year}/annual.pdf     - verifier letter
```

Auth: `require_workspace_role("member")` on the read routes,
`require_workspace_role("admin")` on the vessel upsert and the recompute
route. Every successful mutation writes an audit row
(`vessel.create`, `bdn.upload`, `emissions.compute`, etc.; add to the
closed `AuditAction` enum in §2.2).

Rate limit: emissions recompute is expensive (touches AIS + the model);
apply the existing per-workspace limiter (`limits.py`) with a
2-per-minute ceiling.

---

## 7. Frontend

New route group: `/emissions/...`. New components under
`apps/web/components/emissions/`:

- `VesselsTable.tsx` — registry, edit-in-place for fuel/speed curve.
- `BdnUploader.tsx` — drop a PDF, see the extracted record, accept/reject.
- `EmissionsHeader.tsx` — the eyebrow + hero figure pattern from the case
  detail revamp; the canonical figure here is "EUAs due: 1,247".
- `EmissionsBreakdown.tsx` — per-fuel + per-leg sortable table.
- `AnnualRollupCard.tsx` — vessels grid + targets vs achieved chart.
- `VerifierExport.tsx` — the two download buttons (xlsx + pdf), matching
  the demurrage ExportPdfButton + ExportDocxButton pattern.

Server-rendered PDF (the verifier letter) is fetched as a binary blob;
unlike the demurrage letter the customer does NOT edit it (verifier-
signed input), so contentEditable is **not** applied.

---

## 8. Tests

### Golden voyage

Hand-worked fixture: an aframax tanker, Rotterdam → Algeciras (intra-EU,
`eu_fraction=1.0`), 9 days at 12 kn average, single VLSFO BDN of 145 mt.
Expected outputs locked in `tests/test_emissions_voyage.py`:

- `co2_tonnes_total ≈ 145 × 3.151 = 456.9`
- `co2e_tonnes_eu  ≈ 456.9` (intra-EU)
- `eu_ets_phase_in_factor = 0.70` for `year=2025`
- `eu_ets_allowances_due ≈ 319.8`
- `fueleu_intensity ≈ 91.16 × (1 + tiny WtT delta)` (compliant for 2025)

### BDN extractor regression

Three committed PDFs (VLSFO, MGO, LNG), expected `BunkerDeliveryNoteRecord`
locked in JSON. Re-run via the same `extract_structured` helper the
demurrage extractor uses.

### Annual rollup banking

Two-year synthetic dataset: year-N is surplus, year-N+1 has a small gap.
Assert that banking applies, carry-out is non-zero, and the verifier
workbook footer shows it correctly.

### Citations gate

Run the verifier narrative without the legal tools enabled; assert every
`CitedAuthority` returned by the model is dropped by the gate.

---

## 9. Operational concerns

- **AIS cost.** Spire is ~€0.50 per vessel-day; cap voyage count per
  pricing tier to keep margin positive. Cache AIS legs aggressively (the
  vessel does not retroactively change its track).
- **Verifier audit trail.** Every recompute must be reproducible. We store
  the `inputs_snapshot` JSON on the report row; the verifier xlsx Inputs
  sheet is generated from it byte-for-byte.
- **Daily EUA price.** A small committed JSONL refreshed by a cron, or
  `EUA_PRICE_EUR` env var fall-back. Stale price > 7 days surfaces a yellow
  banner on the rollup; do not block compute.
- **Quarterly rule update.** When EU updates the FuelEU factor table or
  amends the targets, we ship a new versioned `factors_<year>.json` and
  bump `regulatory_year` defaults. Verifier-final files (after 30
  September of year+1) are frozen.
- **Privacy.** Vessel particulars are not PII; the BDN sender + delivery
  port is operational and audit-class. No customer document leaves the
  workspace.

---

## 10. Phasing

| Phase | Scope | Outcome |
| --- | --- | --- |
| **A (3-4 weeks)** | Vessel registry + BDN extractor + per-voyage compute against committed fixture data. AIS distance entered manually in the UI. | A customer with a CSV of BDNs and a known voyage can produce a voyage report. Verifier xlsx works. |
| **B (+2 weeks)** | AIS aggregator wired to Spire (paid). EU-fraction auto-computed. | Customer uploads BDN + clicks "Compute" with no manual distance. |
| **C (+1 week)** | Annual rollup + verifier letter PDF + workbook export. | A workspace can produce its full FY annual report. |
| **D (+2 weeks)** | Pooling + banking + borrowing math; daily EUA price cron; per-fleet dashboard. | Multi-vessel customer manages compliance posture across the year. |
| **E (later)** | Verifier sign-off integration (DNV / LR API or PDF handover). | One-click submission. |

End to end: ~8-10 weeks to a paying design partner; pricing per the
roadmap (EUR 50-100 per voyage, EUR 5-15k/year per fleet).

---

## 11. Owners

- Backend (sections 3-6, 8, 9): dkall.
- Frontend (section 7): Roman.
- Infra (Spire account, AIS cost budget, daily EUA price cron): Panos.
- Regulatory liaison (factor table maintenance, verifier outreach):
  founder + first design partner.

---

## 12. Risk register

| Risk | Mitigation |
| --- | --- |
| Regulation amendment mid-year | Versioned `factors_<year>.json`; verifier-final files frozen at year+1 Sep 30. |
| Spire / MarineTraffic rate limits or cost spike | Cache AIS legs forever; cap voyages per tier; fall-back to customer-entered distance. |
| Customer BDN PDFs are scanned images | Reuse the OCR fall-back planned for the demurrage extractor (§1.1 polish list); flag BDN for human review when extraction confidence is low. |
| Verifier rejects our workbook format | First design partner is a co-design partner; iterate the workbook shape with their verifier in week 9-10. |
| EUA daily price feed goes stale | Yellow banner > 7 days, `EUA_PRICE_EUR` env override, customer can correct on the rollup screen. |
| Pool member workspace deletes a vessel mid-year | Lock vessels enrolled in a pool against deletion; require explicit "withdraw from pool" action. |

---

## 13. What is deliberately not in this plan

- IMO Carbon Intensity Indicator (CII) reporting. Different forms, IMO
  not EU; revisit after the first paying customer asks.
- Voluntary carbon-offset marketplace integration. Out of scope.
- Real-time bunker telemetry. We rely on BDNs (the customer's existing
  flow); a sensor-feed integration is a year-2 sub-product.
- A trading desk. We compute allowances due; we do not buy or sell them.
