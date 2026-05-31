// TypeScript mirror of apps/api/portside_api/schemas.py (notes/04-schemas.md).
// Field names match the wire JSON (snake_case; from/to on laytime rows).

export type Perspective = "owner" | "charterer";

export type PipelineStage =
  | "uploaded"
  | "extracting"
  | "calculating"
  | "analyzing"
  | "drafting"
  | "done"
  | "error"
  | "pending"
  | "rejected"
  | "settled";

export interface ClauseExcerpt {
  clause_no: string;
  text: string;
}

export type CharterPartyForm =
  | "ASBATANKVOY"
  | "GENCON"
  | "NYPE93"
  | "SHELLVOY"
  | "BPVOY"
  | "OTHER";

export interface CharterParty {
  form: CharterPartyForm;
  cp_date: string;
  vessel_name: string;
  owner: string;
  charterer: string;
  load_port: string;
  discharge_port: string;
  laytime_allowed_hours: number;
  laytime_basis: string;
  demurrage_rate_eur_per_day: number;
  despatch_rate_eur_per_day: number | null;
  exception_clauses: string[];
  nor_tender_window: string;
  laytime_commencement_rule: string;
  time_bar_days: number | null;
  time_bar_basis: string;
  clause_excerpts: ClauseExcerpt[];
}

export interface NoticeOfReadiness {
  tendered_at: string;
  accepted_at: string | null;
  tendered_by: string;
  tendered_to: string;
  location: string;
  free_pratique_granted_at: string | null;
  berth_status_at_tender: string | null;
}

export type EventCategory =
  | "arrival"
  | "nor"
  | "free_pratique"
  | "laytime_start"
  | "berthing"
  | "ops_start"
  | "ops_resume"
  | "stoppage_weather"
  | "stoppage_equipment"
  | "stoppage_shift"
  | "stoppage_other"
  | "ops_end"
  | "documents"
  | "departure"
  | "other";

export interface SoFEvent {
  id: string;
  timestamp: string;
  description: string;
  category: EventCategory;
}

export interface StatementOfFacts {
  port: string;
  timezone: string;
  events: SoFEvent[];
}

export interface ExtractionResult {
  charter_party: CharterParty;
  notice_of_readiness: NoticeOfReadiness;
  statement_of_facts: StatementOfFacts;
}

export type LaytimeRowStatus = "laytime" | "excepted" | "demurrage";

export interface EventClassification {
  event_id: string;
  counts_against_laytime: boolean;
  applicable_exception: string | null;
  clause_basis: string;
  reasoning: string;
  contestable: boolean;
}

export interface LaytimeRow {
  from: string;
  to: string;
  duration_hours: number;
  counts: boolean;
  status: LaytimeRowStatus;
  reason: string;
  running_total_hours: number;
  event_id_start: string;
  event_id_end: string;
  contestable: boolean;
}

export interface LaytimeResult {
  laytime_allowed_hours: number;
  laytime_used_hours: number;
  time_on_demurrage_hours: number;
  time_excepted_hours: number;
  demurrage_rate_per_hour_eur: number;
  demurrage_due_eur: number;
  despatch_due_eur: number | null;
  rows: LaytimeRow[];
  classifications: EventClassification[];
}

export interface FlaggedEvent {
  event_id: string;
  title: string;
  summary: string;
  owner_argument: string;
  charterer_argument: string;
  owner_position_strength: number;
  incremental_demurrage_eur: number;
  clauses_cited: string[];
  evidence_required: string[];
}

export interface DisputeAnalysis {
  perspective: Perspective;
  overall_confidence: number;
  narrative_paragraphs: string[];
  flagged_events: FlaggedEvent[];
}

export interface ClaimPacket {
  quantum_eur: number;
  executive_summary: string;
  dispute_narrative_markdown: string;
  claim_letter_markdown: string;
  supporting_documents: string[];
  time_bar_date: string;
  submitted_within_time_bar: boolean;
  days_until_time_bar: number;
}

export interface VoyageState {
  voyage_id: string;
  perspective: Perspective;
  stage: PipelineStage;
  error: string | null;
  created_at: string;
  extraction: ExtractionResult | null;
  laytime: LaytimeResult | null;
  dispute: DisputeAnalysis | null;
  packet: ClaimPacket | null;
}

// Lightweight list-row projection of a VoyageState (GET /voyages). Fields that
// depend on a completed pipeline are nullable for still-processing voyages.
export interface VoyageSummary {
  id: string;
  vessel_name: string | null;
  load_port: string | null;
  discharge_port: string | null;
  quantum_eur: number | null;
  stage: PipelineStage;
  perspective: Perspective;
  created_at: string;
}

// Aggregate of all voyages sharing a vessel_name (GET /vessels). total_quantum_eur
// is null when no constituent voyage has a quantum yet; latest_stage/last_activity
// come from the most-recent voyage by created_at.
export interface VesselSummary {
  name: string;
  voyage_count: number;
  total_quantum_eur: number | null;
  latest_stage: PipelineStage;
  last_activity: string;
  perspectives: Perspective[];
}

// ---------------------------------------------------------------------------
// Email subsystem (W2, notes/architecture_weeks_5_to_8.md §1.3)
// ---------------------------------------------------------------------------

// Wire model mirror of portside_api/email/models.py. The PDF attachment is a
// stretch and is uploaded as multipart in a future variant of the route; v0.1
// emails the markdown letter body inline.
export interface LetterEmailRequest {
  to: string[];
  cc: string[];
  bcc: string[];
  subject?: string;
  preamble_markdown?: string;
}

export interface SesSendResult {
  ses_message_id: string;
  sent_at: string;
  to: string[];
  cc: string[];
  bcc: string[];
  subject: string;
  sandbox: boolean;
}

// Stable enum used by the backend EmailSendError.code field. The route surfaces
// these as {detail: {code, message}}; the UI uses the code to render an
// actionable toast.
export type EmailErrorCode =
  | "SES_UNVERIFIED_RECIPIENT"
  | "SES_THROTTLED"
  | "SES_REJECTED"
  | "SES_TRANSPORT"
  | "SES_NOT_CONFIGURED";

// Error thrown by sendClaimLetter when the backend returns 4xx/5xx with a
// JSON {code, message} body. Lets the caller render a friendly toast.
export interface EmailSendError {
  code: EmailErrorCode | "UNKNOWN";
  message: string;
  status: number;
}

// ---------------------------------------------------------------------------
// Evidence checklist (W3, notes/architecture_weeks_5_to_8.md §1.4)
// ---------------------------------------------------------------------------

// Wire model mirror of portside_api/evidence_checklist.py. ``attached`` is
// deterministic on the backend (uploaded CP -> cp_excerpt rows attached;
// research bundle covering an event -> the weather row attached); the UI just
// renders it.
export type EvidenceRole =
  | "cp_excerpt"
  | "nor"
  | "sof"
  | "bunker_note"
  | "port_log"
  | "weather_observation"
  | "agent_correspondence"
  | "other";

export interface EvidenceItem {
  role: EvidenceRole;
  label: string;
  supports_event_id: string | null;
  supports_clause: string | null;
  attached: boolean;
  source_voyage_doc_id?: string | null;
  note?: string | null;
}

export interface EvidenceChecklist {
  items: EvidenceItem[];
}
