"""The demo voyage fixture, MT Aegean Pioneer, Ras Tanura -> Rotterdam.

SINGLE SOURCE OF TRUTH for the demo scenario, kept identical to the frontend's
`apps/web/lib/demo.ts` and to `apps/web/DESIGN.md` "Demo content". The pipeline
stub replays this; Track A's real pipeline replaces the stub behind the same
signature.

Reconciliation (internally consistent):

    demurrage rate      EUR 45,000 / day  ==  EUR 1,875 / hour
    laytime allowed     72.0 h
    laytime used        117.0 h
    time on demurrage   117.0 - 72.0 = 45.0 h
    quantum             45.0 h * EUR 1,875/h  =  EUR 84,375.00

The contested row is e6->e7 (a 4h weather stoppage on 17 May). Owner contends CP
clause 14 (precipitation > 0.5 mm/hr) is not met, so the time counts.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .schemas import (
    CharterParty,
    ClaimPacket,
    ClauseExcerpt,
    DisputeAnalysis,
    EventClassification,
    ExtractionResult,
    FlaggedEvent,
    LaytimeResult,
    LaytimeRow,
    NoticeOfReadiness,
    Perspective,
    PipelineStage,
    SoFEvent,
    StatementOfFacts,
    VoyageState,
)

DEMURRAGE_RATE_PER_DAY = 45000.0
DEMURRAGE_RATE_PER_HOUR = DEMURRAGE_RATE_PER_DAY / 24.0  # 1875.0
LAYTIME_ALLOWED_HOURS = 72.0
LAYTIME_USED_HOURS = 117.0
TIME_EXCEPTED_HOURS = 0.0
TIME_ON_DEMURRAGE_HOURS = LAYTIME_USED_HOURS - LAYTIME_ALLOWED_HOURS  # 45.0
QUANTUM_EUR = round(TIME_ON_DEMURRAGE_HOURS * DEMURRAGE_RATE_PER_HOUR, 2)  # 84375.0


def _charter_party() -> CharterParty:
    return CharterParty(
        form="ASBATANKVOY",
        cp_date="2026-02-12",
        vessel_name="MT Aegean Pioneer",
        owner="Aegean Tankers S.A.",
        charterer="North Sea Crude Trading B.V.",
        load_port="Ras Tanura",
        discharge_port="Rotterdam",
        laytime_allowed_hours=LAYTIME_ALLOWED_HOURS,
        laytime_basis="SHINC",
        demurrage_rate_eur_per_day=DEMURRAGE_RATE_PER_DAY,
        despatch_rate_eur_per_day=22500.0,
        exception_clauses=["WIBON", "WIFPON", "SHINC"],
        nor_tender_window="Any time, day or night, SHINC",
        laytime_commencement_rule=(
            "6 hours after tender of NOR or upon commencement of cargo ops, whichever earlier"
        ),
        time_bar_days=90,
        time_bar_basis="from completion of discharge",
        clause_excerpts=[
            ClauseExcerpt(
                clause_no="6",
                text=(
                    "Laytime shall commence 6 hours after tender of Notice of Readiness, "
                    "berth or no berth, or upon commencement of cargo operations, whichever "
                    "first occurs."
                ),
            ),
            ClauseExcerpt(
                clause_no="14",
                text=(
                    "Time lost due to rain or other weather conditions shall not count as "
                    "laytime only where precipitation at the place of discharge exceeds 0.5 mm "
                    "per hour for the period claimed. The burden of demonstrating such "
                    "conditions rests with the charterer."
                ),
            ),
        ],
    )


def _notice_of_readiness() -> NoticeOfReadiness:
    return NoticeOfReadiness(
        tendered_at="2026-05-14T06:00:00+02:00",
        accepted_at="2026-05-14T06:00:00+02:00",
        tendered_by="Master, MT Aegean Pioneer",
        tendered_to="North Sea Crude Trading B.V.",
        location="Rotterdam Maasvlakte anchorage",
        free_pratique_granted_at="2026-05-14T07:30:00+02:00",
        berth_status_at_tender="berth occupied",
    )


def _statement_of_facts() -> StatementOfFacts:
    return StatementOfFacts(
        port="Rotterdam",
        timezone="Europe/Amsterdam",
        events=[
            SoFEvent(id="e1", timestamp="2026-05-14T05:00:00+02:00", description="Arrived at Maasvlakte anchorage", category="arrival"),
            SoFEvent(id="e2", timestamp="2026-05-14T06:00:00+02:00", description="NOR tendered", category="nor"),
            SoFEvent(id="e3", timestamp="2026-05-14T12:00:00+02:00", description="Laytime commenced", category="laytime_start"),
            SoFEvent(id="e4", timestamp="2026-05-14T20:00:00+02:00", description="All fast at berth", category="berthing"),
            SoFEvent(id="e5", timestamp="2026-05-14T22:00:00+02:00", description="Commenced discharge", category="ops_start"),
            SoFEvent(id="e6", timestamp="2026-05-17T12:00:00+02:00", description="Stoppage, rain claimed by charterer", category="stoppage_weather"),
            SoFEvent(id="e7", timestamp="2026-05-17T16:00:00+02:00", description="Resumed discharge", category="ops_resume"),
            SoFEvent(id="e8", timestamp="2026-05-19T09:00:00+02:00", description="Completed discharge", category="ops_end"),
        ],
    )


def _extraction() -> ExtractionResult:
    return ExtractionResult(
        charter_party=_charter_party(),
        notice_of_readiness=_notice_of_readiness(),
        statement_of_facts=_statement_of_facts(),
    )


def _classifications() -> list[EventClassification]:
    return [
        EventClassification(
            event_id="e6",
            counts_against_laytime=True,
            applicable_exception="weather",
            clause_basis="CP clause 14 (weather exception, precipitation > 0.5mm/hr)",
            reasoning=(
                "Charterer claims a 4-hour rain stoppage. Per CP clause 14, weather stoppages "
                "are excepted only where precipitation exceeded 0.5 mm/hr. The Rotterdam Port "
                "Authority record shows 0.2 mm/hr at the relevant times, so the exception is "
                "not met and the time counts."
            ),
            contestable=True,
        ),
        EventClassification(
            event_id="e8",
            counts_against_laytime=True,
            applicable_exception=None,
            clause_basis="operational time, no exception applicable",
            reasoning="Standard discharge operations, fully chargeable.",
            contestable=False,
        ),
    ]


def _laytime_rows() -> list[LaytimeRow]:
    return [
        LaytimeRow.model_validate(
            {"from": "2026-05-14T12:00:00+02:00", "to": "2026-05-14T20:00:00+02:00", "duration_hours": 8.0, "counts": True, "status": "laytime", "reason": "Laytime, pre-berth", "running_total_hours": 8.0, "event_id_start": "e3", "event_id_end": "e4", "contestable": False}
        ),
        LaytimeRow.model_validate(
            {"from": "2026-05-14T20:00:00+02:00", "to": "2026-05-14T22:00:00+02:00", "duration_hours": 2.0, "counts": True, "status": "laytime", "reason": "Laytime, at berth", "running_total_hours": 10.0, "event_id_start": "e4", "event_id_end": "e5", "contestable": False}
        ),
        LaytimeRow.model_validate(
            {"from": "2026-05-14T22:00:00+02:00", "to": "2026-05-17T12:00:00+02:00", "duration_hours": 62.0, "counts": True, "status": "laytime", "reason": "Laytime, discharge ops (allowance exhausted at 72h)", "running_total_hours": 72.0, "event_id_start": "e5", "event_id_end": "e6", "contestable": False}
        ),
        LaytimeRow.model_validate(
            {"from": "2026-05-17T12:00:00+02:00", "to": "2026-05-17T16:00:00+02:00", "duration_hours": 4.0, "counts": True, "status": "demurrage", "reason": "Contested, weather, CP clause 14", "running_total_hours": 76.0, "event_id_start": "e6", "event_id_end": "e7", "contestable": True}
        ),
        LaytimeRow.model_validate(
            {"from": "2026-05-17T16:00:00+02:00", "to": "2026-05-19T09:00:00+02:00", "duration_hours": 41.0, "counts": True, "status": "demurrage", "reason": "On demurrage, discharge ops", "running_total_hours": 117.0, "event_id_start": "e7", "event_id_end": "e8", "contestable": False}
        ),
    ]


def _laytime() -> LaytimeResult:
    return LaytimeResult(
        laytime_allowed_hours=LAYTIME_ALLOWED_HOURS,
        laytime_used_hours=LAYTIME_USED_HOURS,
        time_on_demurrage_hours=TIME_ON_DEMURRAGE_HOURS,
        time_excepted_hours=TIME_EXCEPTED_HOURS,
        demurrage_rate_per_hour_eur=DEMURRAGE_RATE_PER_HOUR,
        demurrage_due_eur=QUANTUM_EUR,
        despatch_due_eur=None,
        rows=_laytime_rows(),
        classifications=_classifications(),
    )


def _dispute(perspective: Perspective) -> DisputeAnalysis:
    return DisputeAnalysis(
        perspective=perspective,
        overall_confidence=0.8,
        narrative_paragraphs=[
            "The total laytime used at Rotterdam exceeded the contractually agreed allowance of "
            "72 hours by 45 hours, placing the vessel on demurrage from 17 May 2026. The "
            "charterer disputes a 4-hour weather stoppage on 17 May, which is the only contested "
            "period in the calculation.",
            "Per CP clause 14, weather stoppages are excepted from laytime only where "
            "precipitation at the place of discharge exceeds 0.5 mm per hour. The Rotterdam Port "
            "Authority precipitation record for 17 May 2026 shows a maximum of 0.2 mm/hr during "
            "the claimed period, below the contractual threshold.",
            "The position is supported by The Mexico 1 [1990] 1 Lloyd's Rep 507, which confirms "
            "that a stoppage must satisfy the express contractual condition before it can be "
            "deducted from laytime. The 4-hour period therefore counts and the full demurrage of "
            "EUR 84,375.00 is due.",
        ],
        flagged_events=[
            FlaggedEvent(
                event_id="e6",
                title="Weather stoppage not supported by precipitation threshold",
                summary=(
                    "Charterer claimed a 4-hour rain stoppage on 17 May 2026. CP clause 14 "
                    "excepts weather only where precipitation exceeds 0.5 mm/hr. The Rotterdam "
                    "Port Authority record shows a maximum of 0.2 mm/hr at the relevant times."
                ),
                owner_argument=(
                    "The stoppage does not meet the 0.5 mm/hr threshold in CP clause 14 and, per "
                    "The Mexico 1 [1990] 1 Lloyd's Rep 507, must count as laytime/demurrage."
                ),
                charterer_argument=(
                    "Discharge was physically suspended due to rain and the master recorded the "
                    "stoppage in the Statement of Facts without protest."
                ),
                owner_position_strength=0.8,
                incremental_demurrage_eur=7500.0,
                clauses_cited=["CP clause 14"],
                evidence_required=[
                    "Rotterdam Port Authority precipitation record for 17 May 2026",
                    "berth-specific rainfall data if available",
                ],
            )
        ],
    )


_LETTER_MARKDOWN = """**Aegean Tankers S.A.**
Akti Miaouli 1, Piraeus 185 35, Greece

19 May 2026

North Sea Crude Trading B.V.
Rotterdam

Dear Sirs,

**Re: Demurrage Claim, MT Aegean Pioneer, Ras Tanura / Rotterdam, CP dated 12 February 2026**

We write further to the captioned charter party in respect of the discharge port call at Rotterdam, completed on 19 May 2026.

**1. Summary of claim**
- Laytime allowed: 72 hours SHINC
- Laytime used: 117 hours
- Time on demurrage: 45 hours
- Demurrage rate: EUR 45,000.00 per day pro rata
- Demurrage due: EUR 84,375.00

**2. Disputed time**
The charterer claims a 4-hour weather stoppage on 17 May 2026. Per CP clause 14, weather is excepted only where precipitation exceeds 0.5 mm/hr. The Rotterdam Port Authority record shows a maximum of 0.2 mm/hr. Per The Mexico 1 [1990] 1 Lloyd's Rep 507, the stoppage must count.

**3. Time bar**
This claim is submitted within the contractual time bar of 90 days from completion of discharge (17 August 2026).

**4. Demand**
We accordingly demand payment of EUR 84,375.00 within 30 days of the date of this letter.

All rights reserved.

Yours faithfully,
For and on behalf of Aegean Tankers S.A.
"""


def _packet() -> ClaimPacket:
    return ClaimPacket(
        quantum_eur=QUANTUM_EUR,
        executive_summary=(
            "Owners claim demurrage of EUR 84,375.00 against charterers in respect of the "
            "discharge port call at Rotterdam on the voyage MT Aegean Pioneer, Ras Tanura / "
            "Rotterdam, CP dated 12 February 2026. The claim turns on a disputed 4-hour weather "
            "stoppage that does not meet the CP clause 14 precipitation threshold."
        ),
        dispute_narrative_markdown=(
            "## Dispute summary\n\n"
            "The total laytime used at Rotterdam exceeded the contractually agreed allowance of "
            "72 hours by 45 hours. The only contested period is a 4-hour weather stoppage on 17 "
            "May 2026. Per CP clause 14, weather is excepted only above 0.5 mm/hr precipitation; "
            "the Rotterdam Port Authority record shows 0.2 mm/hr. The position is supported by "
            "*The Mexico 1* [1990] 1 Lloyd's Rep 507."
        ),
        claim_letter_markdown=_LETTER_MARKDOWN,
        supporting_documents=[
            "Charter Party dated 12 February 2026",
            "Notice of Readiness tendered 14 May 2026 at 0600 LT",
            "Statement of Facts signed by Master and port agent",
            "Rotterdam Port Authority precipitation record for 17 May 2026",
        ],
        time_bar_date="2026-08-17",
        submitted_within_time_bar=True,
        days_until_time_bar=81,
    )


def demo_voyage_fixture(
    voyage_id: str = "v_aegean_pioneer",
    perspective: Perspective = "owner",
) -> VoyageState:
    """Return the fully-populated demo VoyageState (stage="done")."""
    return VoyageState(
        voyage_id=voyage_id,
        perspective=perspective,
        stage="done",
        extraction=_extraction(),
        laytime=_laytime(),
        dispute=_dispute(perspective),
        packet=_packet(),
    )


def _variant_fixture(
    voyage_id: str,
    *,
    vessel_name: str,
    load_port: str,
    discharge_port: str,
    stage: PipelineStage,
    created_at: datetime,
    quantum_eur: float | None = None,
    include_packet: bool = True,
) -> VoyageState:
    """A demo voyage on a different vessel/route/stage, built off the base packet.

    Overrides the vessel, ports, quantum and stage so the dashboard shows a row
    per claim status. ``include_packet=False`` models a voyage still being drafted
    (extraction present, no packet yet -> no quantum), for the "In progress" row.
    """
    base = demo_voyage_fixture(voyage_id, "owner")
    assert base.extraction is not None and base.packet is not None
    cp = base.extraction.charter_party.model_copy(
        update={
            "vessel_name": vessel_name,
            "load_port": load_port,
            "discharge_port": discharge_port,
        }
    )
    extraction = base.extraction.model_copy(update={"charter_party": cp})
    update: dict[str, object] = {
        "stage": stage,
        "extraction": extraction,
        "created_at": created_at,
    }
    if include_packet:
        update["packet"] = base.packet.model_copy(
            update={"quantum_eur": quantum_eur if quantum_eur is not None else base.packet.quantum_eur}
        )
    else:
        update["packet"] = None
    return base.model_copy(update=update)


def seed_voyages() -> list[VoyageState]:
    """Demo cases loaded into the store on startup so the dashboard is populated.

    All from a single (owner) perspective, a real user is one party, not both.
    Deliberately one-to-MANY: a vessel runs many voyages, each with its own claim,
    so the /vessels view (one row per vessel, claims + quantum aggregated) reads
    as clearly distinct from /cases (one row per claim). A variable number of
    claims per vessel (Aegean ×3, Ionian ×4, Baltic ×2, Levant ×1) makes that
    one-to-many obvious, and the mix covers every status
    (In progress / Draft / Pending / Rejected / Settled).
    """

    def utc(*args: int) -> datetime:
        return datetime(*args, tzinfo=timezone.utc)

    # MT Aegean Pioneer, 3 claims. The first is the full hero case (the live
    # demo letter); the others are prior voyages in later lifecycle stages.
    aegean = [
        demo_voyage_fixture("v_aegean_pioneer", "owner").model_copy(
            update={"created_at": utc(2026, 5, 19, 9, 0)}
        ),
        _variant_fixture(
            "v_aegean_pioneer_2",
            vessel_name="MT Aegean Pioneer",
            load_port="Ras Tanura",
            discharge_port="Augusta",
            stage="pending",
            created_at=utc(2026, 5, 8, 14, 0),
            quantum_eur=56200.0,
        ),
        _variant_fixture(
            "v_aegean_pioneer_3",
            vessel_name="MT Aegean Pioneer",
            load_port="Ras Tanura",
            discharge_port="Rotterdam",
            stage="settled",
            created_at=utc(2026, 3, 28, 10, 0),
            quantum_eur=71000.0,
        ),
    ]

    # MT Ionian Star, 4 claims, including one still being drafted (no quantum).
    ionian = [
        _variant_fixture(
            "v_ionian_star",
            vessel_name="MT Ionian Star",
            load_port="Novorossiysk",
            discharge_port="Trieste",
            stage="drafting",
            created_at=utc(2026, 5, 18, 7, 30),
            include_packet=False,
        ),
        _variant_fixture(
            "v_ionian_star_2",
            vessel_name="MT Ionian Star",
            load_port="Novorossiysk",
            discharge_port="Trieste",
            stage="pending",
            created_at=utc(2026, 5, 16, 13, 0),
            quantum_eur=61200.0,
        ),
        _variant_fixture(
            "v_ionian_star_3",
            vessel_name="MT Ionian Star",
            load_port="Constanta",
            discharge_port="Genoa",
            stage="done",
            created_at=utc(2026, 5, 12, 11, 0),
            quantum_eur=29900.0,
        ),
        _variant_fixture(
            "v_ionian_star_4",
            vessel_name="MT Ionian Star",
            load_port="Constanta",
            discharge_port="Trieste",
            stage="settled",
            created_at=utc(2026, 3, 15, 9, 0),
            quantum_eur=44800.0,
        ),
    ]

    # MT Baltic Trader, 2 claims.
    baltic = [
        _variant_fixture(
            "v_baltic_trader_settled",
            vessel_name="MT Baltic Trader",
            load_port="Primorsk",
            discharge_port="Wilhelmshaven",
            stage="settled",
            created_at=utc(2026, 5, 2, 11, 0),
            quantum_eur=52250.0,
        ),
        _variant_fixture(
            "v_baltic_trader_2",
            vessel_name="MT Baltic Trader",
            load_port="Primorsk",
            discharge_port="Rotterdam",
            stage="rejected",
            created_at=utc(2026, 4, 20, 15, 0),
            quantum_eur=38500.0,
        ),
    ]

    # MT Levant Carrier, 1 claim, still in progress.
    levant = [
        _variant_fixture(
            "v_levant_carrier",
            vessel_name="MT Levant Carrier",
            load_port="Sidi Kerir",
            discharge_port="Algeciras",
            stage="drafting",
            created_at=utc(2026, 5, 17, 8, 0),
            include_packet=False,
        ),
    ]

    return [*aegean, *ionian, *baltic, *levant]
