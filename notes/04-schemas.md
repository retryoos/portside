# Data Schemas — the integration contract

> Freeze this by 11:00 on May 28th. After freeze, any change needs all three engineers to agree. The whole pipeline is glued together by these shapes; if they drift, integration fails.

The schemas below are written as Pydantic v2 Python models. Track C's TypeScript types are generated from these (or hand-mirrored if generation is fiddly). Track A and Track B both consume and produce them.

---

## 1. The top-level voyage state machine

```python
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field


Perspective = Literal["owner", "charterer"]
PipelineStage = Literal["uploaded", "extracting", "calculating", "analyzing", "drafting", "done", "error"]


class VoyageState(BaseModel):
    voyage_id: str
    perspective: Perspective
    stage: PipelineStage
    error: Optional[str] = None

    extraction: Optional["ExtractionResult"] = None
    laytime: Optional["LaytimeResult"] = None
    dispute: Optional["DisputeAnalysis"] = None
    packet: Optional["ClaimPacket"] = None
```

The frontend polls `GET /voyages/{id}` and gets back the full `VoyageState`. Each agent fills in the corresponding field as it completes.

---

## 2. ExtractionResult — output of Agent 1

```python
class ClauseExcerpt(BaseModel):
    clause_no: str
    text: str


class CharterParty(BaseModel):
    form: Literal["ASBATANKVOY", "GENCON", "NYPE93", "SHELLVOY", "BPVOY", "OTHER"]
    cp_date: str                              # ISO-8601 date
    vessel_name: str
    owner: str
    charterer: str
    load_port: str
    discharge_port: str
    laytime_allowed_hours: float
    laytime_basis: str                        # e.g., "SHINC", "WWDSHEX"
    demurrage_rate_usd_per_day: float
    despatch_rate_usd_per_day: Optional[float] = None
    exception_clauses: list[str]              # e.g., ["WIBON", "WIFPON", "SHINC"]
    nor_tender_window: str                    # free text
    laytime_commencement_rule: str            # free text — e.g., "6 hours after NOR"
    time_bar_days: Optional[int] = 90
    time_bar_basis: str = "from completion of discharge"
    clause_excerpts: list[ClauseExcerpt]


class NoticeOfReadiness(BaseModel):
    tendered_at: datetime
    accepted_at: Optional[datetime] = None
    tendered_by: str
    tendered_to: str
    location: str
    free_pratique_granted_at: Optional[datetime] = None
    berth_status_at_tender: Optional[str] = None    # "berth available" | "berth occupied" | ...


EventCategory = Literal[
    "arrival",
    "nor",
    "free_pratique",
    "laytime_start",
    "berthing",
    "ops_start",
    "ops_resume",
    "stoppage_weather",
    "stoppage_equipment",
    "stoppage_shift",
    "stoppage_other",
    "ops_end",
    "documents",
    "departure",
    "other",
]


class SoFEvent(BaseModel):
    id: str                              # "e1", "e2", ...
    timestamp: datetime
    description: str
    category: EventCategory


class StatementOfFacts(BaseModel):
    port: str
    timezone: str                        # IANA, e.g., "Europe/Athens"
    events: list[SoFEvent]


class ExtractionResult(BaseModel):
    charter_party: CharterParty
    notice_of_readiness: NoticeOfReadiness
    statement_of_facts: StatementOfFacts
```

---

## 3. LaytimeResult — output of Agent 2

```python
LaytimeRowStatus = Literal["laytime", "excepted", "demurrage"]


class EventClassification(BaseModel):
    """Agent 2a's LLM output, one per SoFEvent. Internal — not exposed to frontend."""
    event_id: str
    counts_against_laytime: bool
    applicable_exception: Optional[str] = None      # "weather" | "shex" | "wibon" | ...
    clause_basis: str
    reasoning: str
    contestable: bool


class LaytimeRow(BaseModel):
    from_ts: datetime = Field(..., alias="from")
    to_ts: datetime = Field(..., alias="to")
    duration_hours: float
    counts: bool
    status: LaytimeRowStatus
    reason: str
    running_total_hours: float
    event_id_start: str
    event_id_end: str
    contestable: bool = False


class LaytimeResult(BaseModel):
    laytime_allowed_hours: float
    laytime_used_hours: float
    time_on_demurrage_hours: float
    time_excepted_hours: float
    demurrage_rate_per_hour_usd: float
    demurrage_due_usd: float
    despatch_due_usd: Optional[float] = None        # if vessel finished early
    rows: list[LaytimeRow]
    classifications: list[EventClassification]      # carry through for Agent 3
```

---

## 4. DisputeAnalysis — output of Agent 3

```python
class FlaggedEvent(BaseModel):
    event_id: str
    title: str
    summary: str
    owner_argument: str
    charterer_argument: str
    owner_position_strength: float                  # 0.0–1.0
    incremental_demurrage_usd: float                # additional $ if this flag is upheld
    clauses_cited: list[str]
    evidence_required: list[str]


class DisputeAnalysis(BaseModel):
    perspective: Perspective
    overall_confidence: float                       # 0.0–1.0
    narrative_paragraphs: list[str]
    flagged_events: list[FlaggedEvent]
```

---

## 5. ClaimPacket — output of Agent 4

```python
class ClaimPacket(BaseModel):
    quantum_usd: float
    executive_summary: str
    dispute_narrative_markdown: str
    claim_letter_markdown: str
    supporting_documents: list[str]
    time_bar_date: str                              # ISO-8601 date
    submitted_within_time_bar: bool
    days_until_time_bar: int                        # negative if past
```

---

## 6. HTTP API surface

```
POST /voyages
  multipart/form-data:
    cp: <pdf>
    nor: <pdf>
    sof: <pdf>
    perspective: "owner" | "charterer"
  →  201  { "voyage_id": "v_abc123" }

GET /voyages/{voyage_id}
  →  200  VoyageState (JSON)

GET /voyages/{voyage_id}/letter.pdf
  →  200  application/pdf

GET /voyages/{voyage_id}/letter.docx
  →  200  application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

---

## 7. Versioning policy during the hackathon

- Schemas live in `apps/api/portside_api/schemas.py`.
- Track C generates TypeScript via `datamodel-code-generator` if cheap; otherwise mirrors by hand in `apps/web/lib/types.ts`.
- Any change to a field name after 11:00 must be announced verbally and pinged in the team chat. No silent renames.
- New fields are fine. Removing or renaming requires consent.

---

## 8. Worked example values (use these in tests and fixtures)

For the demo scenario `athens-weather-dispute`:

```json
{
  "voyage_id": "v_athens_weather",
  "perspective": "owner",
  "stage": "done",
  "extraction": { ...see Agent 1 output in 03-agents.md... },
  "laytime": {
    "laytime_allowed_hours": 72,
    "laytime_used_hours": 89.5,
    "time_on_demurrage_hours": 17.5,
    "time_excepted_hours": 11.0,
    "demurrage_rate_per_hour_usd": 2000,
    "demurrage_due_usd": 35000,
    "rows": [
      {
        "from": "2026-05-08T13:00:00+03:00",
        "to": "2026-05-09T02:00:00+03:00",
        "duration_hours": 13.0,
        "counts": true,
        "status": "laytime",
        "reason": "operational",
        "running_total_hours": 13.0,
        "event_id_start": "e3",
        "event_id_end": "e4",
        "contestable": false
      }
    ]
  },
  "dispute": { ...see Agent 3 output in 03-agents.md... },
  "packet": { ...see Agent 4 output in 03-agents.md... }
}
```
