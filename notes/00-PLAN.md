# Portside — Master Plan

> **If you read one doc, read this one.** It's the spine. Everything else is depth.

---

## 1. What we are building, in one sentence

**Portside turns a contested port call into a ready-to-send demurrage resolution in minutes.**

Three PDFs in (Charter Party excerpt, Statement of Facts, Notice of Readiness). One legally-structured claim packet out (laytime calculation table, dispute narrative, claim quantum, formal claim letter), in under 60 seconds.

## 2. Why this idea, why this room

- **Athens.** Piraeus is the largest port in the Mediterranean. Greece controls ~20% of global merchant fleet tonnage. The judges (a Florent × Panathēnea hackathon, with a shipping-industry adjudicator validated by a maritime executive) will understand the pain personally.
- **Real revenue.** A VLCC sitting idle is $30,000–$80,000/day in demurrage. Industry exposure runs into the billions annually. This is not productivity — it's revenue recovery and legal defense, the highest-ROI workflow AI agents can address.
- **A clean wedge.** Maritime AI today is concentrated in vessel tracking, route optimization, port congestion, and emissions. Nobody has gone deep on the document-heavy, legally-precise laytime/demurrage workflow. The closest tools are Excel templates and specialist P&I advisors — neither is a software product.
- **Validated.** A shipping company executive saw it. Their shipping-industry judge contact saw it. Both responded positively. We are not selling a hypothesis; we are sharpening a validated wedge.

## 3. The user and the moment of value

**User:** A claims executive at a ship operator, a charterer's operations team, or a maritime lawyer. The person who today opens a folder with three PDFs and a calculator and starts a two-day process.

**Moment of value:** They drag three PDFs onto the screen. Sixty seconds later the screen shows:
- a per-event laytime calculation table with running totals,
- the contested rows flagged with one-line reasons and a confidence score,
- the dollar amount their position is worth in big text at the bottom,
- a one-click button to generate a formal BIMCO-style claim letter as PDF.

Two-day process collapsed into one minute. That is the demo.

## 4. What makes this defensible (and what the judge will check)

The shipping-industry judge will not be impressed by "AI does the calculation." Every Excel-jockey says that. They will be impressed by:

1. **Legal defensibility.** Every line in the laytime table cites the specific charter party clause that justifies it (e.g., "exception applied: clause 17, SHEX"). Every dispute argument cites the SoF event reference and the clause it relies on. Output should read like a junior associate at Ince, Hill Dickinson, or HFW wrote it.
2. **Numerical reliability.** The arithmetic is done in deterministic Python, not by an LLM. The LLM classifies; Python sums. We say this explicitly in the demo because a maritime professional will distrust an LLM doing arithmetic.
3. **BIMCO conformance.** The output letter uses BIMCO-standard formal language, references the right standard form (ASBATANKVOY / NYPE 93 / GENCON / Shellvoy), and includes the required components: claim quantum, time bar compliance statement, supporting document list.
4. **Audit trail.** Every figure is traceable back to a specific event in a specific source document. No hidden math.
5. **Time-bar awareness.** Demurrage claims are typically subject to a strict contractual time bar (often 90 days from completion of discharge, all original supporting documents). Portside surfaces the time-bar clock the moment the voyage is opened. Missing it forfeits the claim — this is the single biggest avoidable mistake in the industry.

These five are the deep-domain "tells" that prove we built the right thing.

## 5. Scope (what we are building)

One voyage, one port call, one disputed laytime calculation, one claim packet. Owner-side perspective (with a stretch toggle for charterer-side rebuttal).

**Inputs:** Charter Party excerpt (laytime + demurrage clauses), Statement of Facts, Notice of Readiness.

**Outputs:**
- Structured laytime calculation table (per-event, with running total)
- Annotated event timeline with exceptions applied
- Plain-language dispute narrative
- Formal BIMCO-style claim letter (PDF + Word)
- Claim quantum in EUR

## 6. Non-goals (explicitly out)

- Multi-port voyages
- Time charters (we do voyage charters only)
- Bunker disputes, cargo damage, General Average
- AIS / port-authority API integrations
- Inbound email automation (post-MVP roadmap, not built)
- Outbound email send (post-MVP roadmap, not built)
- User accounts, persistence beyond a single session
- Mobile

If anything is unclear during the day, the test is: "does this help us get a clean five-minute demo at 19:00?" If no, it is out.

## 7. The four-agent pipeline (one paragraph)

Agent 1 (**Classifier + Extractor**) ingests the three PDFs, identifies which is which, and extracts structured fields with Claude tool-use against a strict JSON schema. Agent 2 (**Laytime Calculator**) takes the structured event timeline and applies exception logic: an LLM step classifies each SoF event against the applicable clauses (SHINC / SHEX / WIBON / WIPON / WWD), then a deterministic Python function walks the events and sums time-used vs time-excepted to produce the laytime table and the quantum. Agent 3 (**Dispute Analyst**) inspects the classified timeline, flags contestable events, generates a legal argument for the owner's position with citations, and assigns a confidence score per flag. Agent 4 (**Claims Drafter**) takes the calculation, the disputes, and the quantum and writes the dispute narrative and the formal claim letter in BIMCO-style language, exportable as PDF and Word.

See [03-agents.md](03-agents.md) for the full specs.

## 8. Tech stack (one paragraph)

Next.js 15 + Tailwind + shadcn/ui frontend rendering the three-panel UI; FastAPI + async Python backend; **`pdfplumber` (MIT) for local PDF text + table extraction** so Claude only ever sees clean text; **Claude Sonnet 4.6 for extraction, classification, dispute reasoning, and drafting** (Opus 4.7 held in reserve as a per-agent quality escape hatch via env var); deterministic Python for the laytime arithmetic; native Claude PDF reading kept only as a fallback when pdfplumber can't parse a document; **the claim-letter PDF is exported client-side in the browser (`html2pdf.js`)** — no server-side PDF library, no native deps. No database — in-memory + temp files for the hackathon. **The demo runs locally (primary); in parallel a background workstream deploys the frontend to AWS Amplify and the backend to AWS App Runner for a live "it's on AWS right now" URL** (AWS sponsors the hackathon). Auth + DB (Supabase) are Phase C only — see [extended_plan.md](extended_plan.md) and [02-architecture.md §12](02-architecture.md#12-hackathon-day-aws-deployment-parallel-flex-off-the-critical-path).

> **Cost note:** pdfplumber + Sonnet 4.6 puts per-voyage spend at ~$0.05–0.10 vs. ~$1.50 for native PDF + Opus 4.7 — a 15–30× reduction at no demo-quality cost on our text-native synthetic data.

See [02-architecture.md](02-architecture.md) for the full stack and data flow.

## 9. The demo (the only thing that matters at 19:00)

Five minutes. Pre-prepared synthetic voyage scenario with a contested weather exception worth ~$22k. The flow:

1. Land on the empty three-panel app. Click **New Voyage Claim**.
2. Drag three PDFs onto the dropzone (already in the demo folder).
3. Show the four agents running in sequence with live status (one to two seconds each, ~30s total).
4. Center panel fills with the per-event laytime table. Right panel shows the dispute narrative. Bottom shows **Demurrage due to owners: EUR 38,400.00** in big text.
5. Click the one contested row. Inline expansion shows: "Charterer claimed 11 hours of weather exception. Port authority weather record shows wind speeds below the 25-knot threshold per CP clause 17. Time should be charged at $200/hr = $2,200 additional recoverable." Confidence: 88%.
6. Click **Generate Claim Letter**. A polished one-page BIMCO-style PDF appears in the right panel.
7. End.

See [08-demo-and-pitch.md](08-demo-and-pitch.md) for the full script and anticipated judge Q&A.

## 10. The day plan (high level)

| Block          | Time            | Outcome                                                                  |
| -------------- | --------------- | ------------------------------------------------------------------------ |
| Build hour 1   | 09:45 – 10:45   | Repo skeletons up, synthetic scenario v0 generated, API contract frozen  |
| Build 2–4      | 10:45 – 13:00   | Track A: extraction works on 1 scenario. Track B: calculator + Agent 3 stub. Track C: panels render dummy data. |
| Lunch          | 13:00 – 14:00   | Eat. Discuss what to cut.                                                |
| Build 5–6      | 14:00 – 15:00   | First end-to-end run (any quality). Mentor check-in at 15:00.            |
| Build 7–9      | 15:00 – 18:00   | Polish: Agent 4 letter quality, dispute narrative, demo-grade UI.        |
| Freeze         | 18:00 – 18:30   | No new features. Only fixing broken demo paths.                          |
| Demo prep      | 18:30 – 19:00   | Rehearse the 5-minute flow twice. Submit.                                |
| Pitch prep     | 19:30 – 20:30   | If finalist: rehearse pitch script.                                      |

See [07-day-plan.md](07-day-plan.md) for the hour-by-hour breakdown by engineer, and [14-parallel-execution-plan.md](14-parallel-execution-plan.md) for the subphase-grained branch fan-out tuned to the agent fleet.

## 11. Team and parallel tracks

Three engineers, three Claude-equipped laptops. Three tracks merging at a single JSON contract:

- **Track A (Ingestion + Extraction):** Owns Agents 1 + 2 (the Laytime Calculator's LLM classifier step and the Python arithmetic). Owns the FastAPI endpoints.
- **Track B (Reasoning + Drafting):** Owns Agents 3 + 4. Owns prompt engineering for dispute analysis and claim letter generation. Owns the BIMCO output templates.
- **Track C (Frontend + Export):** Owns the three-panel UI, the demo flow, the PDF/Word export, and the demo polish.

The contract between them is [04-schemas.md](04-schemas.md). Freeze it by 11:00 and stop changing it.

## 12. Risks and explicit cuts

| Risk                                          | Mitigation                                                                                          |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Extraction is flaky on real-looking PDFs      | Use synthetic PDFs that we generated; we control the layout. Don't try to handle a real Shell SoF.  |
| LLM gets the laytime arithmetic wrong         | Arithmetic is in Python, not the LLM. We say this explicitly in the demo.                           |
| Demo crashes mid-run                          | Pre-record a fallback video at 18:00. Keep a JSON of the "happy path" output to load if the live run fails. |
| Out of time on Agent 4 (claim letter)         | Hard-coded BIMCO letter template with slot-filling from the calculator output. No free-form drafting if behind. |
| UI looks janky                                | Use shadcn/ui defaults. No custom design. Three panels, clean typography, that's it.                |
| Time bar logic too complex to ship            | Hard-code 90-day time bar from completion of discharge. One badge, no logic branches.               |

If we are behind at 17:00, the cut order is:
1. Word export (keep PDF only)
2. Charterer-side rebuttal toggle
3. Confidence scores (just say "contested" / "supported")
4. The inline contested-row explanation (just show the dispute narrative as static text)

## 13. Beyond the hackathon (one paragraph, for the pitch)

Day-one revenue is a SaaS seat for ship operators, charterers, and maritime lawyers at $500–$2,000/month. Greece alone has hundreds of ship management companies and small penetration is a meaningful ARR. Motion two is the AI-native service play YC has been writing about — we handle the claim as a service, taking a success fee on recovered demurrage. Motion three is adjacent document-heavy maritime workflows: cargo damage, freight disputes, charter party breach, P&I correspondence. Every voyage processed trains a fleet-specific company brain on preferred clause language and historical dispute outcomes — a proprietary dataset no competitor can replicate from scratch.

## 14. Open questions to resolve before 09:45

- [ ] Confirm we have Claude Sonnet 4.6 API access on every fleet laptop (and Opus 4.7 reachable as the per-agent quality escape hatch)
- [ ] Decide ASBATANKVOY vs GENCON as the demo charter form (recommendation: **ASBATANKVOY** — tanker, more dramatic dollar figures)
- [ ] Confirm we are demoing from a local laptop, not a deployed URL
- [ ] Decide the demo voyage's vessel name and route (recommendation: a VLCC, Ras Tanura → Piraeus, the Piraeus reference will land in the room)
- [ ] Decide one fictional company name on the claim letter sender/recipient lines
