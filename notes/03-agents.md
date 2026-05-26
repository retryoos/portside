# Agent Specifications

> Four agents. Each one has a single, narrow purpose. Read the I/O contract before writing the prompt — the contract is in [04-schemas.md](04-schemas.md) and is shared with Track C's TypeScript types.

---

## Agent 1 — Document Classifier & Extractor

### Purpose
Take three uploaded PDFs of unknown order and produce a single structured JSON object representing the voyage: which doc is the CP, the NOR, the SoF; the key fields from each; the full SoF event timeline.

### Model
Claude Opus 4.7. One call, native PDF input, tool-use with `strict: true`.

### Input
- Three PDFs (as base64 content blocks)
- The `voyage_id` (for logging)
- The `perspective` ("owner" or "charterer") — affects no extraction but is passed through

### Output (the `ExtractionResult` schema)
```json
{
  "charter_party": {
    "form": "ASBATANKVOY",
    "cp_date": "2026-04-12",
    "vessel_name": "MV ANTHEM OF PIRAEUS",
    "owner": "Hellas Shipping Co.",
    "charterer": "Mediterranean Crude Trading",
    "load_port": "Ras Tanura",
    "discharge_port": "Piraeus",
    "laytime_allowed_hours": 72,
    "laytime_basis": "SHINC",
    "demurrage_rate_usd_per_day": 48000,
    "despatch_rate_usd_per_day": 24000,
    "exception_clauses": ["WIBON", "WIFPON", "SHINC"],
    "nor_tender_window": "Any time, day or night, SHINC",
    "laytime_commencement_rule": "6 hours after tender of NOR or upon commencement of cargo ops, whichever earlier",
    "time_bar_days": 90,
    "time_bar_basis": "from completion of discharge",
    "clause_excerpts": [
      {"clause_no": "6", "text": "Laytime shall commence 6 hours after..."},
      {"clause_no": "17", "text": "Time lost due to weather conditions causing wind speeds in excess of 25 knots..."}
    ]
  },
  "notice_of_readiness": {
    "tendered_at": "2026-05-08T07:00:00+03:00",
    "accepted_at": "2026-05-08T07:00:00+03:00",
    "tendered_by": "Master, MV Anthem of Piraeus",
    "tendered_to": "Mediterranean Crude Trading",
    "location": "Piraeus customary anchorage",
    "free_pratique_granted_at": "2026-05-08T08:30:00+03:00",
    "berth_status_at_tender": "berth occupied"
  },
  "statement_of_facts": {
    "port": "Piraeus",
    "timezone": "Europe/Athens",
    "events": [
      {"id": "e1", "timestamp": "2026-05-08T06:30:00+03:00", "description": "Arrived at customary anchorage", "category": "arrival"},
      {"id": "e2", "timestamp": "2026-05-08T07:00:00+03:00", "description": "NOR tendered", "category": "nor"},
      {"id": "e3", "timestamp": "2026-05-08T13:00:00+03:00", "description": "Laytime commenced", "category": "laytime_start"},
      {"id": "e4", "timestamp": "2026-05-09T02:00:00+03:00", "description": "All fast at berth", "category": "berthing"},
      {"id": "e5", "timestamp": "2026-05-09T04:00:00+03:00", "description": "Commenced discharge", "category": "ops_start"},
      {"id": "e6", "timestamp": "2026-05-10T11:00:00+03:00", "description": "Stoppage — rain claimed by charterer", "category": "stoppage_weather"},
      {"id": "e7", "timestamp": "2026-05-10T22:00:00+03:00", "description": "Resumed discharge", "category": "ops_resume"},
      {"id": "e8", "timestamp": "2026-05-12T18:00:00+03:00", "description": "Completed discharge", "category": "ops_end"}
    ]
  }
}
```

### Prompt strategy
- System prompt: "You are a maritime documents analyst. Extract structured fields from these three documents. Identify which document is the Charter Party, which is the Notice of Readiness, and which is the Statement of Facts. Use the provided tool to return the result. Be precise about timestamps — preserve the timezone offset shown in the documents. Do not infer values that are not stated."
- Single user message: "[CP PDF] [NOR PDF] [SoF PDF]"
- Tool: `record_voyage_extraction` with the schema above.

### Failure modes & defenses
- **PDF order ambiguous** — the prompt forces explicit classification.
- **Missing field** — schema marks all fields nullable except vessel/owner/charterer. Don't fail hard.
- **Timestamp without timezone** — assume port-local based on the SoF port; flag with `timezone_inferred: true`.

### Prompt cache
The system prompt and tool schema are cache-eligible across calls.

---

## Agent 2 — Laytime Calculator

### Purpose
Take the extracted timeline and produce the per-event laytime table, the total time used, the time on demurrage, and the dollar quantum.

This is the most important agent. Get this wrong and the rest is irrelevant.

### Implementation
**Two-step:** an LLM classifier step (Opus 4.7) followed by a deterministic Python function. The LLM does not do arithmetic.

### Step 2a — Event classification (LLM)

#### Input
- The `ExtractionResult` from Agent 1 (or just the CP exception clauses + the SoF events)
- The `perspective`

#### Output (one entry per SoF event)
```json
[
  {
    "event_id": "e6",
    "counts_against_laytime": false,
    "applicable_exception": "weather",
    "clause_basis": "CP clause 17 (weather exception, wind > 25kt)",
    "reasoning": "Charterer claims rain stoppage. Per CP clause 17, weather stoppages count only if wind speeds exceeded 25 knots. Classification is provisional pending corroboration from independent weather record.",
    "contestable": true
  },
  {
    "event_id": "e8",
    "counts_against_laytime": true,
    "applicable_exception": null,
    "clause_basis": "operational time, no exception applicable",
    "reasoning": "Standard discharge operations, fully chargeable.",
    "contestable": false
  }
]
```

#### Prompt strategy
- Provide all CP exception clauses and basis (SHINC/SHEX/WIBON/etc.) in the system prompt.
- Provide all SoF events in a single user message.
- Use tool-use with a list-of-objects schema.
- One LLM call for all events (not one per event).

### Step 2b — Arithmetic (deterministic Python)

```python
def calculate_laytime(
    extraction: ExtractionResult,
    classifications: list[EventClassification],
) -> LaytimeResult:
    # Walk events in chronological order from laytime_start to ops_end.
    # For each (event_n, event_n+1) pair, compute the duration.
    # If event_n is classified as counting against laytime, add to time_used.
    # If excepted, add to time_excepted with reason.
    # Track running total. When running total exceeds laytime_allowed, vessel is on demurrage.
    # Once on demurrage, exceptions stop applying (unless CP says otherwise — we hard-code the
    # standard rule for the hackathon).
    # Output the per-row table + summary.
```

The output schema is `LaytimeResult` in [04-schemas.md](04-schemas.md). The key fields:

```json
{
  "laytime_allowed_hours": 72,
  "laytime_used_hours": 89.5,
  "time_on_demurrage_hours": 17.5,
  "demurrage_rate_per_hour_usd": 2000,
  "demurrage_due_usd": 35000,
  "rows": [
    {
      "from": "2026-05-08T13:00:00+03:00",
      "to": "2026-05-09T02:00:00+03:00",
      "duration_hours": 13.0,
      "counts": true,
      "running_total_hours": 13.0,
      "status": "laytime",
      "reason": "operational",
      "event_id_start": "e3",
      "event_id_end": "e4"
    },
    ...
  ]
}
```

### Why this split
A maritime professional will not trust an LLM to add up hours. They will trust Python. We say this in the demo: "the arithmetic is deterministic — the LLM only classifies."

---

## Agent 3 — Dispute Analyst

### Purpose
For each event the calculator flagged as `contestable: true`, generate the legal argument for the owner's (or charterer's) position, with citations.

### Model
Claude Opus 4.7.

### Input
- `ExtractionResult`
- `LaytimeResult` (from Agent 2)
- The classifications with `contestable: true`
- `perspective` ("owner" or "charterer")

### Output (`DisputeAnalysis` schema)
```json
{
  "perspective": "owner",
  "overall_confidence": 0.84,
  "narrative_paragraphs": [
    "The total laytime used in this discharge exceeds the contractually agreed allowance by 17.5 hours, primarily driven by the disputed weather stoppage at e6...",
    "...",
    "..."
  ],
  "flagged_events": [
    {
      "event_id": "e6",
      "title": "Weather exception claim not supported by clause threshold",
      "summary": "Charterer claimed an 11-hour weather stoppage. CP clause 17 admits weather exceptions only when wind speeds exceed 25 knots. The port authority weather record for 2026-05-10 shows peak gusts of 18 knots and no rain at the relevant times.",
      "owner_argument": "The stoppage does not meet the contractual threshold in CP clause 17 and should be charged at the demurrage rate.",
      "charterer_argument": "Local conditions on the berth were worse than the port-wide record; the master agreed in writing to the stoppage.",
      "owner_position_strength": 0.88,
      "incremental_demurrage_usd": 2200,
      "clauses_cited": ["CP clause 17"],
      "evidence_required": ["port authority meteorological record", "berth-specific wind data if available"]
    }
  ]
}
```

### Prompt strategy
- System prompt establishes the agent as "a senior maritime claims analyst preparing a defensible demurrage dispute brief."
- Provide the CP clause excerpts inline (cache-eligible).
- Output via tool-use with the `DisputeAnalysis` schema.
- For each flagged event, require both `owner_argument` and `charterer_argument` (we will only display the perspective the user chose, but having both helps the model be more honest).

### Tone and citations
The narrative must read like a junior associate at a maritime law firm wrote it. Specific clause numbers. Specific event IDs. Specific dollar increments. No marketing speak.

---

## Agent 4 — Claims Drafter

### Purpose
Take the calculator output and the dispute analysis and produce:
1. A multi-paragraph dispute narrative (already partially available from Agent 3; here it is refined and formatted).
2. A formal BIMCO-style claim letter as Markdown (will be rendered to PDF/Word).

### Model
Claude Opus 4.7 (Sonnet 4.6 as fallback if behind on time).

### Input
- `ExtractionResult`
- `LaytimeResult`
- `DisputeAnalysis`
- `perspective`

### Output (`ClaimPacket` schema)
```json
{
  "quantum_usd": 35000,
  "executive_summary": "Owners claim demurrage of USD 35,000 against charterers in respect of the discharge port call at Piraeus on the voyage MV Anthem of Piraeus, Ras Tanura / Piraeus, CP dated 12 April 2026.",
  "dispute_narrative_markdown": "## Dispute summary\n\nThe total laytime used in this discharge exceeded the contractually agreed allowance of 72 hours by 17.5 hours...",
  "claim_letter_markdown": "[Owner letterhead]\n\n12 May 2026\n\nMediterranean Crude Trading\n...\n\nDear Sirs,\n\n**Re: Demurrage Claim — MV Anthem of Piraeus — Ras Tanura / Piraeus — CP dated 12 April 2026**\n\nWe write further to the captioned charter party to claim demurrage in the amount of USD 35,000 in respect of the discharge port call at Piraeus...",
  "supporting_documents": [
    "Charter Party dated 12 April 2026",
    "Notice of Readiness tendered 8 May 2026 at 0700 LT",
    "Statement of Facts signed by Master and port agent",
    "Port authority weather record for 10 May 2026"
  ],
  "time_bar_date": "2026-08-10",
  "submitted_within_time_bar": true
}
```

### Prompt strategy
- System prompt: "You are drafting a formal demurrage claim letter in BIMCO-style language. You write for a recipient who is a professional charterer's claims officer or maritime lawyer. Be precise, formal, and avoid filler."
- Provide the BIMCO letter skeleton template inline.
- Stream the response so the frontend can render letter content live.

### Letter template skeleton (loaded as `apps/api/portside_api/letter_template.html`)

```
[Owner letterhead block]
[Date]

[Recipient block]

Dear Sirs,

Re: Demurrage Claim — MV {VESSEL} — {LOAD_PORT} / {DISCHARGE_PORT} — CP dated {CP_DATE}

We write further to the captioned charter party in respect of the discharge port call at {DISCHARGE_PORT}, which was completed on {DISCHARGE_COMPLETION_DATE}.

1. Summary of claim
   - Laytime allowed: {LAYTIME_ALLOWED_HOURS} hours {LAYTIME_BASIS}
   - Laytime used: {LAYTIME_USED_HOURS} hours
   - Time on demurrage: {TIME_ON_DEMURRAGE_HOURS} hours
   - Demurrage rate: USD {DEMURRAGE_RATE_PER_DAY} per day pro rata
   - Demurrage due: USD {QUANTUM}

2. Statement of facts
   {NARRATIVE_PARAGRAPHS}

3. Disputed time
   {DISPUTED_EVENTS_BLOCK}

4. Time bar
   This claim is submitted within the contractual time bar of {TIME_BAR_DAYS} days from completion of discharge ({TIME_BAR_DATE}).

5. Supporting documents
   {SUPPORTING_DOCS_LIST}

6. Demand
   We accordingly demand payment of USD {QUANTUM} within 30 days of the date of this letter to the account details previously notified.

All rights reserved.

Yours faithfully,
[Claims executive]
[Owner company]
```

The drafter fills the slots and produces the markdown / HTML version. PDF render is done by `weasyprint` outside the agent.

---

## Cross-cutting prompt engineering rules

1. **Schemas are the contract.** Every agent uses tool-use with `strict: true`. We do not parse free-form text outputs.
2. **Cite clauses by number wherever possible.** "Per CP clause 17" beats "per the weather clause."
3. **Cite events by ID.** "Event e6 (Stoppage — rain claimed by charterer)" beats "the rain stoppage."
4. **Prefer Opus 4.7 for the demo.** Use Sonnet 4.6 only if we are over budget on latency.
5. **Cache the CP text.** Pass it as a cache-control block in every agent call after Agent 1.
6. **Stream Agent 4.** The visual of the letter generating live is part of the demo.
