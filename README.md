# Portside

**Maritime Demurrage & Laytime Resolution Agent** — built at the Florent × Panathēnea Hackathon, Athens, May 28th 2026.

> One voyage document bundle in. One legally-structured demurrage claim packet out.

---

## The Problem

Every time a vessel finishes a port call and laytime is disputed, a maritime claims team spends 2–4 days pulling together the Charter Party, the Statement of Facts, and the Notice of Readiness, manually calculating which hours count against laytime and which don't, arguing over weather exceptions, and producing a claim letter that may or may not recover what's owed. A single VLCC sitting idle costs $30,000–$80,000 per day. The industry's annual demurrage exposure is in the billions.

This is a revenue recovery and legal defense problem — the highest-value category of workflow an AI agent can address.

## What We're Building

A four-agent pipeline that takes three PDF inputs (Charter Party excerpt, Statement of Facts, Notice of Readiness) and produces a complete demurrage claim package in under 60 seconds:

1. **Document Classifier & Extractor** — identifies each document and extracts structured fields (laytime allowed, demurrage rate, NOR tender/acceptance times, all SoF events with timestamps, exception clauses like SHINC / SHEX / WIBON / WIPON).
2. **Laytime Calculator** — applies charter party rules mechanically with deterministic Python arithmetic to guarantee numerical reliability. Produces a per-event table showing time used, time excepted, time credited, and running total.
3. **Dispute Analyst** — flags contested events (ambiguous NOR tender language, disputed weather periods, port congestion claims, deviation from BIMCO conventions), generates legal arguments for both sides, assigns a confidence score.
4. **Claims Drafter** — produces the laytime calculation summary, dispute narrative, claim quantum, and a formal BIMCO-style claim letter exportable as PDF or Word.

## MVP Scope (12 hours)

One voyage, one port call, one disputed laytime calculation, one claim packet. No multi-port voyages, no bunker disputes, no General Average. Done cleanly.

**Inputs:** Charter Party excerpt (laytime & demurrage clauses), Statement of Facts, Notice of Readiness.
**Outputs:** Structured laytime calculation table, annotated event timeline with exceptions applied, plain-language dispute narrative, formal claim letter.

## Architecture

- **Models:** Claude Opus 4.7 / Sonnet 4.6 for extraction, classification, reasoning, and drafting; deterministic Python for the laytime arithmetic.
- **Backend:** FastAPI, async Python, tool-use with strict JSON schemas.
- **Frontend:** Next.js + Tailwind. Three-panel UI — document extracts on the left, interactive laytime timeline in the center, generated claim package on the right.
- **Target latency:** under 45 seconds end-to-end on three documents.

## Demo Flow

1. Click **New Voyage Claim**, upload three PDFs.
2. Watch the four agents run sequentially with live status messages.
3. Center panel fills with the laytime calculation table; right panel shows the dispute narrative; bottom shows the claim quantum in large text (e.g. `Demurrage due to owners: USD 38,400.00`).
4. Highlight a contested row — agent explains inline why the charterer's weather exception isn't supported.
5. Click **Generate Claim Letter** — a polished BIMCO-style PDF appears.

Under five minutes. Every step is real.

## Data Strategy

- **Charter party templates:** BIMCO public forms (ASBATANKVOY, NYPE 93, GENCON, Shellvoy).
- **Domain rules:** International Group of P&I Clubs educational material; TotalEnergies and Shell public voyage charter guidance.
- **Synthetic voyage scenarios:** generated in the first hour from BIMCO templates — contested NOR tender, disputed weather, SHINC vs SHEX interpretation, port congestion.

No proprietary dataset needed for the demo.

## Why This Wedge

Existing maritime AI is concentrated in vessel tracking, route optimization, port congestion, and emissions. None go deep on the document-heavy, legally-precise, calculation-intensive laytime workflow because it requires understanding charter party clauses, NOR rules, SoF conventions, port holiday schedules, weather exceptions, and BIMCO forms simultaneously — exactly the kind of multi-document reasoning modern agents are built for. The closest existing tools are Excel templates and specialist P&I advisors. Neither is a software product.

Athens is the right room. Piraeus is the largest port in the Mediterranean and Greece controls ~20% of global merchant fleet tonnage. The judges will understand this pain personally.

## Team

Three engineers, three laptops, Claude Max + Claude Pro + a third agent stack. Parallel tracks:

- **Track A:** Ingestion & parsing pipeline (Agents 1 + 2)
- **Track B:** Agent chain & output generation (Agents 3 + 4)
- **Track C:** Frontend, three-panel UI, export flow

Tracks merge at a single FastAPI JSON boundary.

## Hackathon Day Schedule (May 28th 2026)

| Time  | Item                                                  |
| ----- | ----------------------------------------------------- |
| 08:00 | Arrival, registration, coffee, networking             |
| 09:00 | Welcome by Florent Venture Partners                   |
| 09:15 | Talks by CEOs of Intrim and Entire.io                 |
| 09:45 | **Start building**                                    |
| 13:00 | Lunch                                                 |
| 15:00 | Mentor check-in                                       |
| 19:00 | **Demo submission**                                   |
| 19:30 | Dinner                                                |
| 20:30 | Finalists pitch, winners announced                    |
| 21:00 | Close                                                 |

## Roadmap Beyond the Hackathon

- **SaaS:** $500–$2,000 per seat per month for ship operators, charterers, maritime lawyers.
- **AI-native service:** per-voyage fee or success fee on recovered demurrage.
- **Adjacent workflows:** cargo damage claims, freight disputes, charter party breach notices, P&I correspondence.
- **Inbound automation:** monitor the claims-executive inbox, detect SoFs / NORs / Charter Parties as email attachments, auto-assemble the voyage bundle before the user opens it.
- **Outbound automation:** send the approved claim letter from the user's own email, log the chain against the voyage record, draft chasers and rebuttals on reply.
