// Canonical demo voyage for the UI — MT Aegean Pioneer, Ras Tanura -> Rotterdam,
// claim USD 84,375.00 (per apps/web/DESIGN.md "Demo content"). Authored here as a
// typed module so it is committed source (survives the shared working tree) and
// type-checked against the API contract. The "Try the demo voyage" button renders
// this offline; the live POST /voyages flow uses the backend's own fixture.
//
// Reconciliation: demurrage USD 45,000/day = USD 1,875/hr; laytime allowed 72h,
// used 117h, on demurrage 45h -> 45 * 1,875 = USD 84,375.00. The contested 4h
// weather stoppage on 17 May is worth 4 * 1,875 = USD 7,500 if the charterer's
// exception is rejected (owner's position).

import type { VoyageState } from "./types";

export const demoVoyage: VoyageState = {
  voyage_id: "v_aegean_pioneer",
  perspective: "owner",
  stage: "done",
  error: null,
  extraction: {
    charter_party: {
      form: "ASBATANKVOY",
      cp_date: "2026-02-12",
      vessel_name: "MT Aegean Pioneer",
      owner: "Aegean Tankers S.A.",
      charterer: "North Sea Crude Trading B.V.",
      load_port: "Ras Tanura",
      discharge_port: "Rotterdam",
      laytime_allowed_hours: 72,
      laytime_basis: "SHINC",
      demurrage_rate_usd_per_day: 45000,
      despatch_rate_usd_per_day: 22500,
      exception_clauses: ["WIBON", "WIFPON", "SHINC"],
      nor_tender_window: "Any time, day or night, SHINC",
      laytime_commencement_rule:
        "6 hours after tender of NOR or upon commencement of cargo ops, whichever earlier",
      time_bar_days: 90,
      time_bar_basis: "from completion of discharge",
      clause_excerpts: [
        {
          clause_no: "6",
          text: "Laytime shall commence 6 hours after tender of Notice of Readiness, berth or no berth, or upon commencement of cargo operations, whichever first occurs.",
        },
        {
          clause_no: "14",
          text: "Time lost due to rain or other weather conditions shall not count as laytime only where precipitation at the place of discharge exceeds 0.5 mm per hour for the period claimed. The burden of demonstrating such conditions rests with the charterer.",
        },
      ],
    },
    notice_of_readiness: {
      tendered_at: "2026-05-14T06:00:00+02:00",
      accepted_at: "2026-05-14T06:00:00+02:00",
      tendered_by: "Master, MT Aegean Pioneer",
      tendered_to: "North Sea Crude Trading B.V.",
      location: "Rotterdam Maasvlakte anchorage",
      free_pratique_granted_at: "2026-05-14T07:30:00+02:00",
      berth_status_at_tender: "berth occupied",
    },
    statement_of_facts: {
      port: "Rotterdam",
      timezone: "Europe/Amsterdam",
      events: [
        { id: "e1", timestamp: "2026-05-14T05:00:00+02:00", description: "Arrived at Maasvlakte anchorage", category: "arrival" },
        { id: "e2", timestamp: "2026-05-14T06:00:00+02:00", description: "NOR tendered", category: "nor" },
        { id: "e3", timestamp: "2026-05-14T12:00:00+02:00", description: "Laytime commenced", category: "laytime_start" },
        { id: "e4", timestamp: "2026-05-14T20:00:00+02:00", description: "All fast at berth", category: "berthing" },
        { id: "e5", timestamp: "2026-05-14T22:00:00+02:00", description: "Commenced discharge", category: "ops_start" },
        { id: "e6", timestamp: "2026-05-17T12:00:00+02:00", description: "Stoppage — rain claimed by charterer", category: "stoppage_weather" },
        { id: "e7", timestamp: "2026-05-17T16:00:00+02:00", description: "Resumed discharge", category: "ops_resume" },
        { id: "e8", timestamp: "2026-05-19T09:00:00+02:00", description: "Completed discharge", category: "ops_end" },
      ],
    },
  },
  laytime: {
    laytime_allowed_hours: 72,
    laytime_used_hours: 117,
    time_on_demurrage_hours: 45,
    time_excepted_hours: 0,
    demurrage_rate_per_hour_usd: 1875,
    demurrage_due_usd: 84375,
    despatch_due_usd: null,
    classifications: [
      { event_id: "e6", counts_against_laytime: true, applicable_exception: "weather", clause_basis: "CP clause 14 (weather exception, precipitation > 0.5mm/hr)", reasoning: "Charterer claims a 4-hour rain stoppage. Per CP clause 14, weather stoppages are excepted only where precipitation exceeded 0.5 mm/hr. The Rotterdam Port Authority record shows 0.2 mm/hr at the relevant times, so the exception is not met and the time counts.", contestable: true },
      { event_id: "e8", counts_against_laytime: true, applicable_exception: null, clause_basis: "operational time, no exception applicable", reasoning: "Standard discharge operations, fully chargeable.", contestable: false },
    ],
    rows: [
      { from: "2026-05-14T12:00:00+02:00", to: "2026-05-14T20:00:00+02:00", duration_hours: 8, counts: true, status: "laytime", reason: "Laytime — pre-berth", running_total_hours: 8, event_id_start: "e3", event_id_end: "e4", contestable: false },
      { from: "2026-05-14T20:00:00+02:00", to: "2026-05-14T22:00:00+02:00", duration_hours: 2, counts: true, status: "laytime", reason: "Laytime — at berth", running_total_hours: 10, event_id_start: "e4", event_id_end: "e5", contestable: false },
      { from: "2026-05-14T22:00:00+02:00", to: "2026-05-17T12:00:00+02:00", duration_hours: 62, counts: true, status: "laytime", reason: "Laytime — discharge ops (allowance exhausted at 72h)", running_total_hours: 72, event_id_start: "e5", event_id_end: "e6", contestable: false },
      { from: "2026-05-17T12:00:00+02:00", to: "2026-05-17T16:00:00+02:00", duration_hours: 4, counts: true, status: "demurrage", reason: "Contested — weather, CP clause 14", running_total_hours: 76, event_id_start: "e6", event_id_end: "e7", contestable: true },
      { from: "2026-05-17T16:00:00+02:00", to: "2026-05-19T09:00:00+02:00", duration_hours: 41, counts: true, status: "demurrage", reason: "On demurrage — discharge ops", running_total_hours: 117, event_id_start: "e7", event_id_end: "e8", contestable: false },
    ],
  },
  dispute: {
    perspective: "owner",
    overall_confidence: 0.8,
    narrative_paragraphs: [
      "The total laytime used at Rotterdam exceeded the contractually agreed allowance of 72 hours by 45 hours, placing the vessel on demurrage from 17 May 2026. The charterer disputes a 4-hour weather stoppage on 17 May, which is the only contested period in the calculation.",
      "Per CP clause 14, weather stoppages are excepted from laytime only where precipitation at the place of discharge exceeds 0.5 mm per hour. The Rotterdam Port Authority precipitation record for 17 May 2026 shows a maximum of 0.2 mm/hr during the claimed period — below the contractual threshold.",
      "The position is supported by The Mexico 1 [1990] 1 Lloyd's Rep 507, which confirms that a stoppage must satisfy the express contractual condition before it can be deducted from laytime. The 4-hour period therefore counts and the full demurrage of USD 84,375.00 is due.",
    ],
    flagged_events: [
      {
        event_id: "e6",
        title: "Weather stoppage not supported by precipitation threshold",
        summary: "Charterer claimed a 4-hour rain stoppage on 17 May 2026. CP clause 14 excepts weather only where precipitation exceeds 0.5 mm/hr. The Rotterdam Port Authority record shows a maximum of 0.2 mm/hr at the relevant times.",
        owner_argument: "The stoppage does not meet the 0.5 mm/hr threshold in CP clause 14 and, per The Mexico 1 [1990] 1 Lloyd's Rep 507, must count as laytime/demurrage.",
        charterer_argument: "Discharge was physically suspended due to rain and the master recorded the stoppage in the Statement of Facts without protest.",
        owner_position_strength: 0.8,
        incremental_demurrage_usd: 7500,
        clauses_cited: ["CP clause 14"],
        evidence_required: [
          "Rotterdam Port Authority precipitation record for 17 May 2026",
          "berth-specific rainfall data if available",
        ],
      },
    ],
  },
  packet: {
    quantum_usd: 84375,
    executive_summary:
      "Owners claim demurrage of USD 84,375.00 against charterers in respect of the discharge port call at Rotterdam on the voyage MT Aegean Pioneer, Ras Tanura / Rotterdam, CP dated 12 February 2026. The claim turns on a disputed 4-hour weather stoppage that does not meet the CP clause 14 precipitation threshold.",
    dispute_narrative_markdown:
      "## Dispute summary\n\nThe total laytime used at Rotterdam exceeded the contractually agreed allowance of 72 hours by 45 hours. The only contested period is a 4-hour weather stoppage on 17 May 2026. Per CP clause 14, weather is excepted only above 0.5 mm/hr precipitation; the Rotterdam Port Authority record shows 0.2 mm/hr. The position is supported by *The Mexico 1* [1990] 1 Lloyd's Rep 507.",
    claim_letter_markdown:
      "**Aegean Tankers S.A.**\nAkti Miaouli 1, Piraeus 185 35, Greece\n\n19 May 2026\n\nNorth Sea Crude Trading B.V.\nRotterdam\n\nDear Sirs,\n\n**Re: Demurrage Claim — MT Aegean Pioneer — Ras Tanura / Rotterdam — CP dated 12 February 2026**\n\nWe write further to the captioned charter party in respect of the discharge port call at Rotterdam, completed on 19 May 2026.\n\n**1. Summary of claim**\n- Laytime allowed: 72 hours SHINC\n- Laytime used: 117 hours\n- Time on demurrage: 45 hours\n- Demurrage rate: USD 45,000.00 per day pro rata\n- Demurrage due: USD 84,375.00\n\n**2. Disputed time**\nThe charterer claims a 4-hour weather stoppage on 17 May 2026. Per CP clause 14, weather is excepted only where precipitation exceeds 0.5 mm/hr. The Rotterdam Port Authority record shows a maximum of 0.2 mm/hr. Per *The Mexico 1* [1990] 1 Lloyd's Rep 507, the stoppage must count.\n\n**3. Time bar**\nThis claim is submitted within the contractual time bar of 90 days from completion of discharge (17 August 2026).\n\n**4. Demand**\nWe accordingly demand payment of USD 84,375.00 within 30 days of the date of this letter.\n\nAll rights reserved.\n\nYours faithfully,\nFor and on behalf of Aegean Tankers S.A.",
    supporting_documents: [
      "Charter Party dated 12 February 2026",
      "Notice of Readiness tendered 14 May 2026 at 0600 LT",
      "Statement of Facts signed by Master and port agent",
      "Rotterdam Port Authority precipitation record for 17 May 2026",
    ],
    time_bar_date: "2026-08-17",
    submitted_within_time_bar: true,
    days_until_time_bar: 81,
  },
};

// ---- Screen 1 (settled case detail) demo data — NOT part of the API contract ----

export interface CorrespondenceItem {
  date: string; // ISO date
  actor: string;
  summary: string;
  detectedFromInbox?: boolean;
  settled?: boolean;
}

export interface CaseOutcome {
  original_claim_usd: number;
  settled_usd: number;
  recovery_pct: number;
  days_to_settlement: number;
  time_bar_status: string;
}

export const demoCorrespondence: CorrespondenceItem[] = [
  { date: "2026-05-20", actor: "Aegean Tankers S.A.", summary: "Demurrage claim submitted to charterer — USD 84,375.00, with laytime calculation and supporting documents." },
  { date: "2026-05-27", actor: "North Sea Crude Trading B.V.", summary: "Charterer response disputing the 4-hour weather stoppage on 17 May.", detectedFromInbox: true },
  { date: "2026-05-29", actor: "Aegean Tankers S.A.", summary: "Rebuttal sent citing CP clause 14 and The Mexico 1 [1990] 1 Lloyd's Rep 507; attached Port Authority precipitation record." },
  { date: "2026-06-05", actor: "North Sea Crude Trading B.V.", summary: "Revised settlement offer of USD 79,000.00." },
  { date: "2026-06-10", actor: "Aegean Tankers S.A.", summary: "Settlement accepted at USD 79,000.00 — 21 days from claim submission.", settled: true },
];

export const demoOutcome: CaseOutcome = {
  original_claim_usd: 84375,
  settled_usd: 79000,
  recovery_pct: 93.6,
  days_to_settlement: 21,
  time_bar_status: "Cleared 67 days early",
};
