"""Pydantic v2 models — the integration contract.

These mirror notes/04-schemas.md §1–§5 exactly. Track C's TypeScript types are
generated from (or hand-mirror) these shapes. Track A and Track B both consume
and produce them. Do not silently rename fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# 1. Top-level voyage state machine
# ---------------------------------------------------------------------------

Perspective = Literal["owner", "charterer"]
PipelineStage = Literal[
    "uploaded",
    "extracting",
    "calculating",
    "analyzing",
    "drafting",
    "done",
    "error",
]


class VoyageState(BaseModel):
    voyage_id: str
    perspective: Perspective
    stage: PipelineStage
    error: Optional[str] = None

    extraction: Optional["ExtractionResult"] = None
    laytime: Optional["LaytimeResult"] = None
    dispute: Optional["DisputeAnalysis"] = None
    packet: Optional["ClaimPacket"] = None


# ---------------------------------------------------------------------------
# 2. ExtractionResult — output of Agent 1
# ---------------------------------------------------------------------------


class ClauseExcerpt(BaseModel):
    clause_no: str
    text: str


class CharterParty(BaseModel):
    form: Literal["ASBATANKVOY", "GENCON", "NYPE93", "SHELLVOY", "BPVOY", "OTHER"]
    cp_date: str  # ISO-8601 date
    vessel_name: str
    owner: str
    charterer: str
    load_port: str
    discharge_port: str
    laytime_allowed_hours: float
    laytime_basis: str  # e.g., "SHINC", "WWDSHEX"
    demurrage_rate_eur_per_day: float
    despatch_rate_eur_per_day: Optional[float] = None
    exception_clauses: list[str]  # e.g., ["WIBON", "WIFPON", "SHINC"]
    nor_tender_window: str  # free text
    laytime_commencement_rule: str  # free text — e.g., "6 hours after NOR"
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
    berth_status_at_tender: Optional[str] = None  # "berth available" | "berth occupied" | ...


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
    id: str  # "e1", "e2", ...
    timestamp: datetime
    description: str
    category: EventCategory


class StatementOfFacts(BaseModel):
    port: str
    timezone: str  # IANA, e.g., "Europe/Athens"
    events: list[SoFEvent]


class ExtractionResult(BaseModel):
    charter_party: CharterParty
    notice_of_readiness: NoticeOfReadiness
    statement_of_facts: StatementOfFacts


# ---------------------------------------------------------------------------
# 3. LaytimeResult — output of Agent 2
# ---------------------------------------------------------------------------

LaytimeRowStatus = Literal["laytime", "excepted", "demurrage"]


class EventClassification(BaseModel):
    """Agent 2a's LLM output, one per SoFEvent. Internal — not exposed to frontend."""

    event_id: str
    counts_against_laytime: bool
    applicable_exception: Optional[str] = None  # "weather" | "shex" | "wibon" | ...
    clause_basis: str
    reasoning: str
    contestable: bool


class LaytimeRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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
    demurrage_rate_per_hour_eur: float
    demurrage_due_eur: float
    despatch_due_eur: Optional[float] = None  # if vessel finished early
    rows: list[LaytimeRow]
    classifications: list[EventClassification]  # carry through for Agent 3


# ---------------------------------------------------------------------------
# 4. DisputeAnalysis — output of Agent 3
# ---------------------------------------------------------------------------


class FlaggedEvent(BaseModel):
    event_id: str
    title: str
    summary: str
    owner_argument: str
    charterer_argument: str
    owner_position_strength: float  # 0.0–1.0
    incremental_demurrage_eur: float  # additional $ if this flag is upheld
    clauses_cited: list[str]
    evidence_required: list[str]


class DisputeAnalysis(BaseModel):
    perspective: Perspective
    overall_confidence: float  # 0.0–1.0
    narrative_paragraphs: list[str]
    flagged_events: list[FlaggedEvent]


# ---------------------------------------------------------------------------
# 5. ClaimPacket — output of Agent 4
# ---------------------------------------------------------------------------


class ClaimPacket(BaseModel):
    quantum_eur: float
    executive_summary: str
    dispute_narrative_markdown: str
    claim_letter_markdown: str
    supporting_documents: list[str]
    time_bar_date: str  # ISO-8601 date
    submitted_within_time_bar: bool
    days_until_time_bar: int  # negative if past


# Resolve forward references on VoyageState.
VoyageState.model_rebuild()
