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

// ---------------------------------------------------------------------------
// Claim strength sub-scores (W4, notes/architecture_weeks_5_to_8.md §1.5)
// ---------------------------------------------------------------------------

// Wire model mirror of portside_api/claim_strength.py. Two of the four
// sub-scores are deterministic backend-side (time_bar_risk + evidence_completeness);
// the UI never needs to know which, since they all arrive as the same closed
// vocabulary word.
export type Strength = "Strong" | "Arguable" | "Weak";

export interface ClaimStrengthSubScores {
  clause_clarity: Strength;
  evidence_completeness: Strength;
  counterparty_pushback_risk: Strength;
  time_bar_risk: Strength;
}

export interface FlaggedEventStrength {
  event_id: string;
  sub_scores: ClaimStrengthSubScores;
}

// ---------------------------------------------------------------------------
// Legal citations (W5, notes/architecture_weeks_5_to_8.md §1.6)
// ---------------------------------------------------------------------------

// Mirrors portside_api/legal/models.py. ``verified_via_tool`` is always true
// on the wire: the backend's verify gate drops anything that did not pass.
// ``tool_used`` carries the channel (currently always "corpus"; "imo" and
// "eur_lex" are wired but not yet emitting).
export type CitedAuthorityTool =
  | "corpus"
  | "lookup"
  | "eur_lex"
  | "imo"
  | "bailii";

export interface CitedAuthority {
  citation: string;
  verified_via_tool: boolean;
  tool_used: CitedAuthorityTool;
  proposition: string;
  url?: string | null;
}

export interface FlaggedEventCitations {
  event_id: string;
  cited_authorities: CitedAuthority[];
}

// ---------------------------------------------------------------------------
// Audit log (W6, notes/architecture_weeks_5_to_8.md §2.2)
// ---------------------------------------------------------------------------

// Closed action vocabulary mirroring portside_api/audit.py. A backend
// addition trips tsc here so the UI never silently renders an unknown
// action.
export type AuditAction =
  | "voyage.create"
  | "voyage.delete"
  | "voyage.status_change"
  | "voyage.revise_apply"
  | "voyage.rebuttal"
  | "voyage.letter_email"
  | "voyage.evidence_refresh"
  | "voyage.from_email"
  | "workspace.create"
  | "workspace.invite"
  | "workspace.accept"
  | "workspace.member_remove";

export type AuditTarget =
  | "voyage"
  | "claim"
  | "workspace"
  | "membership"
  | "invitation";

export interface AuditEvent {
  id: number;
  actor_sub: string | null;
  // Wire field is a free str (the backend Pydantic model loosens the
  // closed Literal to str for forward compatibility); the closed union
  // above is what the UI actually expects to render.
  action: AuditAction | string;
  target_type: AuditTarget | string;
  target_id: string;
  at: string;
  payload: Record<string, unknown>;
}
