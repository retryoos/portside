"""Worked-example fixture: the ``athens-weather-dispute`` demo scenario.

This builds a fully-populated ``VoyageState`` (stage="done") using the values
from notes/04-schemas.md §8 and the agent-output examples in notes/03-agents.md.

The numbers are internally consistent:

    demurrage rate      USD 48,000 / day  ==  USD 2,000 / hour
    laytime allowed     72.0 h
    laytime used        91.2 h   (counting rows below)
    time excepted        9.8 h
    time on demurrage   91.2 - 72.0 = 19.2 h
    quantum             19.2 h * USD 2,000/h  =  USD 38,400.00

The contested row is e6->e7 (the 11h weather stoppage). From the owner's
perspective it is treated as counting against laytime; the charterer disputes
it. Upholding the owner's position is already reflected in the quantum.
"""

from __future__ import annotations

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
    SoFEvent,
    StatementOfFacts,
    VoyageState,
)

DEMURRAGE_RATE_PER_DAY = 48000.0
DEMURRAGE_RATE_PER_HOUR = DEMURRAGE_RATE_PER_DAY / 24.0  # 2000.0
LAYTIME_ALLOWED_HOURS = 72.0
LAYTIME_USED_HOURS = 91.2
TIME_EXCEPTED_HOURS = 9.8
TIME_ON_DEMURRAGE_HOURS = LAYTIME_USED_HOURS - LAYTIME_ALLOWED_HOURS  # 19.2
QUANTUM_USD = round(TIME_ON_DEMURRAGE_HOURS * DEMURRAGE_RATE_PER_HOUR, 2)  # 38400.0


def _charter_party() -> CharterParty:
    return CharterParty(
        form="ASBATANKVOY",
        cp_date="2026-04-12",
        vessel_name="MV Anthem of Piraeus",
        owner="Hellas Shipping Co.",
        charterer="Mediterranean Crude Trading",
        load_port="Ras Tanura",
        discharge_port="Piraeus",
        laytime_allowed_hours=LAYTIME_ALLOWED_HOURS,
        laytime_basis="SHINC",
        demurrage_rate_usd_per_day=DEMURRAGE_RATE_PER_DAY,
        despatch_rate_usd_per_day=24000.0,
        exception_clauses=["WIBON", "WIFPON", "SHINC"],
        nor_tender_window="Any time, day or night, SHINC",
        laytime_commencement_rule=(
            "6 hours after tender of NOR or upon commencement of cargo ops, "
            "whichever earlier"
        ),
        time_bar_days=90,
        time_bar_basis="from completion of discharge",
        clause_excerpts=[
            ClauseExcerpt(
                clause_no="6",
                text=(
                    "Laytime shall commence 6 hours after tender of Notice of "
                    "Readiness or upon commencement of cargo operations, "
                    "whichever is earlier, whether in berth or not."
                ),
            ),
            ClauseExcerpt(
                clause_no="17",
                text=(
                    "Time lost due to weather conditions causing wind speeds in "
                    "excess of 25 knots at the place of loading or discharge shall "
                    "not count as laytime or as time on demurrage."
                ),
            ),
        ],
    )


def _notice_of_readiness() -> NoticeOfReadiness:
    return NoticeOfReadiness(
        tendered_at="2026-05-08T07:00:00+03:00",
        accepted_at="2026-05-08T07:00:00+03:00",
        tendered_by="Master, MV Anthem of Piraeus",
        tendered_to="Mediterranean Crude Trading",
        location="Piraeus customary anchorage",
        free_pratique_granted_at="2026-05-08T08:30:00+03:00",
        berth_status_at_tender="berth occupied",
    )


def _statement_of_facts() -> StatementOfFacts:
    events = [
        SoFEvent(
            id="e1",
            timestamp="2026-05-08T06:30:00+03:00",
            description="Arrived at customary anchorage",
            category="arrival",
        ),
        SoFEvent(
            id="e2",
            timestamp="2026-05-08T07:00:00+03:00",
            description="NOR tendered",
            category="nor",
        ),
        SoFEvent(
            id="e3",
            timestamp="2026-05-08T13:00:00+03:00",
            description="Laytime commenced",
            category="laytime_start",
        ),
        SoFEvent(
            id="e4",
            timestamp="2026-05-09T02:00:00+03:00",
            description="All fast at berth",
            category="berthing",
        ),
        SoFEvent(
            id="e5",
            timestamp="2026-05-09T04:00:00+03:00",
            description="Commenced discharge",
            category="ops_start",
        ),
        SoFEvent(
            id="e6",
            timestamp="2026-05-10T11:00:00+03:00",
            description="Stoppage — rain claimed by charterer",
            category="stoppage_weather",
        ),
        SoFEvent(
            id="e7",
            timestamp="2026-05-10T22:00:00+03:00",
            description="Resumed discharge",
            category="ops_resume",
        ),
        SoFEvent(
            id="e8",
            timestamp="2026-05-11T07:48:00+03:00",
            description="Suspended for berth congestion / shift (uncontested)",
            category="stoppage_shift",
        ),
        SoFEvent(
            id="e9",
            timestamp="2026-05-12T18:00:00+03:00",
            description="Completed discharge",
            category="ops_end",
        ),
    ]
    return StatementOfFacts(
        port="Piraeus",
        timezone="Europe/Athens",
        events=events,
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
            clause_basis="CP clause 17 (weather exception, wind > 25kt)",
            reasoning=(
                "Charterer claims an 11-hour rain stoppage. Per CP clause 17, "
                "weather stoppages count against laytime unless wind speeds "
                "exceeded 25 knots. The port authority record for 2026-05-10 "
                "shows peak gusts of 18 knots, so the exception is not met and "
                "the time counts against the charterer. Classification is "
                "provisional pending corroboration."
            ),
            contestable=True,
        ),
        EventClassification(
            event_id="e8",
            counts_against_laytime=False,
            applicable_exception="shex",
            clause_basis="Agreed shift/congestion suspension, uncontested",
            reasoning=(
                "Berth congestion suspension agreed in writing by both parties; "
                "excepted from laytime. Not in dispute."
            ),
            contestable=False,
        ),
        EventClassification(
            event_id="e9",
            counts_against_laytime=True,
            applicable_exception=None,
            clause_basis="operational time, no exception applicable",
            reasoning="Standard discharge operations, fully chargeable.",
            contestable=False,
        ),
    ]


def _laytime_rows() -> list[LaytimeRow]:
    # Counting rows accumulate the running total. The vessel crosses onto
    # demurrage once the running total exceeds 72.0 h, which happens inside the
    # e8->e9 span (split at the 72h crossover at 2026-05-11T22:48:00+03:00).
    return [
        LaytimeRow.model_validate(
            {
                "from": "2026-05-08T13:00:00+03:00",
                "to": "2026-05-09T02:00:00+03:00",
                "duration_hours": 13.0,
                "counts": True,
                "status": "laytime",
                "reason": "operational",
                "running_total_hours": 13.0,
                "event_id_start": "e3",
                "event_id_end": "e4",
                "contestable": False,
            }
        ),
        LaytimeRow.model_validate(
            {
                "from": "2026-05-09T02:00:00+03:00",
                "to": "2026-05-09T04:00:00+03:00",
                "duration_hours": 2.0,
                "counts": True,
                "status": "laytime",
                "reason": "operational (waiting to commence discharge)",
                "running_total_hours": 15.0,
                "event_id_start": "e4",
                "event_id_end": "e5",
                "contestable": False,
            }
        ),
        LaytimeRow.model_validate(
            {
                "from": "2026-05-09T04:00:00+03:00",
                "to": "2026-05-10T11:00:00+03:00",
                "duration_hours": 31.0,
                "counts": True,
                "status": "laytime",
                "reason": "operational (discharge)",
                "running_total_hours": 46.0,
                "event_id_start": "e5",
                "event_id_end": "e6",
                "contestable": False,
            }
        ),
        LaytimeRow.model_validate(
            {
                "from": "2026-05-10T11:00:00+03:00",
                "to": "2026-05-10T22:00:00+03:00",
                "duration_hours": 11.0,
                "counts": True,
                "status": "laytime",
                "reason": (
                    "contested weather stoppage — owner contends CP cl.17 "
                    "threshold (25kt) not met, so time counts"
                ),
                "running_total_hours": 57.0,
                "event_id_start": "e6",
                "event_id_end": "e7",
                "contestable": True,
            }
        ),
        LaytimeRow.model_validate(
            {
                "from": "2026-05-10T22:00:00+03:00",
                "to": "2026-05-11T07:48:00+03:00",
                "duration_hours": 9.8,
                "counts": False,
                "status": "excepted",
                "reason": "agreed berth-congestion / shift suspension (uncontested)",
                "running_total_hours": 57.0,
                "event_id_start": "e7",
                "event_id_end": "e8",
                "contestable": False,
            }
        ),
        LaytimeRow.model_validate(
            {
                "from": "2026-05-11T07:48:00+03:00",
                "to": "2026-05-11T22:48:00+03:00",
                "duration_hours": 15.0,
                "counts": True,
                "status": "laytime",
                "reason": "operational (discharge) — laytime exhausted at end of row",
                "running_total_hours": 72.0,
                "event_id_start": "e8",
                "event_id_end": "e9",
                "contestable": False,
            }
        ),
        LaytimeRow.model_validate(
            {
                "from": "2026-05-11T22:48:00+03:00",
                "to": "2026-05-12T18:00:00+03:00",
                "duration_hours": 19.2,
                "counts": True,
                "status": "demurrage",
                "reason": "operational (discharge) — vessel on demurrage",
                "running_total_hours": 91.2,
                "event_id_start": "e8",
                "event_id_end": "e9",
                "contestable": False,
            }
        ),
    ]


def _laytime() -> LaytimeResult:
    return LaytimeResult(
        laytime_allowed_hours=LAYTIME_ALLOWED_HOURS,
        laytime_used_hours=LAYTIME_USED_HOURS,
        time_on_demurrage_hours=TIME_ON_DEMURRAGE_HOURS,
        time_excepted_hours=TIME_EXCEPTED_HOURS,
        demurrage_rate_per_hour_usd=DEMURRAGE_RATE_PER_HOUR,
        demurrage_due_usd=QUANTUM_USD,
        despatch_due_usd=None,
        rows=_laytime_rows(),
        classifications=_classifications(),
    )


def _dispute(perspective: Perspective) -> DisputeAnalysis:
    return DisputeAnalysis(
        perspective=perspective,
        overall_confidence=0.84,
        narrative_paragraphs=[
            (
                "The total laytime used in the discharge of MV Anthem of Piraeus "
                "at Piraeus was 91.2 hours against a contractual allowance of 72 "
                "hours SHINC, placing the vessel on demurrage for 19.2 hours at "
                "the agreed rate of USD 48,000 per day pro rata, a quantum of "
                "USD 38,400.00."
            ),
            (
                "The principal contested item is the 11-hour stoppage at event e6 "
                "(2026-05-10 11:00 LT), recorded as 'rain claimed by charterer'. "
                "CP clause 17 admits weather exceptions only where wind speeds "
                "exceed 25 knots. The port authority meteorological record for "
                "2026-05-10 shows peak gusts of 18 knots, below the contractual "
                "threshold, so the stoppage counts against the charterer."
            ),
            (
                "The 9.8-hour suspension at event e8 for berth congestion is "
                "treated as excepted by agreement of both parties and has been "
                "excluded from laytime; it is not in dispute. On the foregoing "
                "basis owners' claim of USD 38,400.00 is considered well founded "
                "and submitted within the 90-day contractual time bar."
            ),
        ],
        flagged_events=[
            FlaggedEvent(
                event_id="e6",
                title="Weather exception claim not supported by clause threshold",
                summary=(
                    "Charterer claimed an 11-hour weather stoppage. CP clause 17 "
                    "admits weather exceptions only when wind speeds exceed 25 "
                    "knots. The port authority weather record for 2026-05-10 "
                    "shows peak gusts of 18 knots and no qualifying conditions at "
                    "the relevant times."
                ),
                owner_argument=(
                    "The stoppage does not meet the contractual threshold in CP "
                    "clause 17 and the 11 hours should be charged at the "
                    "demurrage rate."
                ),
                charterer_argument=(
                    "Local conditions on the berth were worse than the port-wide "
                    "record; the master acknowledged the stoppage on the SoF."
                ),
                owner_position_strength=0.88,
                incremental_demurrage_usd=22000.0,
                clauses_cited=["CP clause 17"],
                evidence_required=[
                    "port authority meteorological record for 2026-05-10",
                    "berth-specific wind data if available",
                ],
            ),
        ],
    )


def _claim_letter_markdown() -> str:
    return (
        "**Hellas Shipping Co.**  \n"
        "Akti Miaouli 12, Piraeus 185 35, Greece\n\n"
        "12 May 2026\n\n"
        "Mediterranean Crude Trading  \n"
        "Attn: Demurrage Claims Department\n\n"
        "Dear Sirs,\n\n"
        "**Re: Demurrage Claim — MV Anthem of Piraeus — Ras Tanura / Piraeus — "
        "CP dated 12 April 2026**\n\n"
        "We write further to the captioned charter party in respect of the "
        "discharge port call at Piraeus, which was completed on 12 May 2026.\n\n"
        "**1. Summary of claim**\n\n"
        "- Laytime allowed: 72.0 hours SHINC\n"
        "- Laytime used: 91.2 hours\n"
        "- Time on demurrage: 19.2 hours\n"
        "- Demurrage rate: USD 48,000 per day pro rata\n"
        "- **Demurrage due: USD 38,400.00**\n\n"
        "**2. Statement of facts**\n\n"
        "Notice of Readiness was tendered at 0700 LT on 8 May 2026 and laytime "
        "commenced at 1300 LT the same day. Discharge proceeded with one "
        "contested weather stoppage of 11 hours (event e6) and one agreed "
        "berth-congestion suspension of 9.8 hours (event e8), which we have "
        "excluded from laytime. Discharge completed at 1800 LT on 12 May 2026.\n\n"
        "**3. Disputed time**\n\n"
        "We do not accept the 11-hour weather stoppage recorded at event e6. "
        "CP clause 17 admits weather exceptions only where wind speeds exceed "
        "25 knots. The Piraeus port authority record for 10 May 2026 shows peak "
        "gusts of 18 knots; the contractual threshold is not met and the time "
        "counts against charterers.\n\n"
        "**4. Time bar**\n\n"
        "This claim is submitted within the contractual time bar of 90 days from "
        "completion of discharge (10 August 2026).\n\n"
        "**5. Supporting documents**\n\n"
        "- Charter Party dated 12 April 2026\n"
        "- Notice of Readiness tendered 8 May 2026 at 0700 LT\n"
        "- Statement of Facts signed by Master and port agent\n"
        "- Port authority weather record for 10 May 2026\n\n"
        "**6. Demand**\n\n"
        "We accordingly demand payment of USD 38,400.00 within 30 days of the "
        "date of this letter to the account details previously notified.\n\n"
        "All rights reserved.\n\n"
        "Yours faithfully,\n\n"
        "For and on behalf of Hellas Shipping Co.  \n"
        "Claims Department"
    )


def _packet() -> ClaimPacket:
    return ClaimPacket(
        quantum_usd=QUANTUM_USD,
        executive_summary=(
            "Owners claim demurrage of USD 38,400.00 against charterers in "
            "respect of the discharge port call at Piraeus on the voyage MV "
            "Anthem of Piraeus, Ras Tanura / Piraeus, CP dated 12 April 2026. "
            "Laytime used was 91.2 hours against an allowance of 72 hours, "
            "placing the vessel on demurrage for 19.2 hours."
        ),
        dispute_narrative_markdown=(
            "## Dispute summary\n\n"
            "The total laytime used in this discharge exceeded the contractually "
            "agreed allowance of 72 hours by 19.2 hours, placing MV Anthem of "
            "Piraeus on demurrage for 19.2 hours at USD 48,000 per day pro rata "
            "(USD 2,000 per hour), a quantum of **USD 38,400.00**.\n\n"
            "### Contested weather stoppage (event e6)\n\n"
            "Charterers recorded an 11-hour rain stoppage on 10 May 2026. CP "
            "clause 17 admits weather exceptions only where wind speeds exceed "
            "25 knots. The Piraeus port authority record shows peak gusts of 18 "
            "knots, below the contractual threshold, so the time counts against "
            "charterers.\n\n"
            "### Agreed suspension (event e8)\n\n"
            "A 9.8-hour berth-congestion suspension was agreed by both parties "
            "and has been excluded from laytime. It is not in dispute."
        ),
        claim_letter_markdown=_claim_letter_markdown(),
        supporting_documents=[
            "Charter Party dated 12 April 2026",
            "Notice of Readiness tendered 8 May 2026 at 0700 LT",
            "Statement of Facts signed by Master and port agent",
            "Port authority weather record for 10 May 2026",
        ],
        time_bar_date="2026-08-10",
        submitted_within_time_bar=True,
        days_until_time_bar=74,
    )


def athens_weather_fixture(voyage_id: str, perspective: Perspective) -> VoyageState:
    """Return a fully-populated ``VoyageState`` for the demo scenario.

    The returned state has ``stage="done"`` with extraction, laytime, dispute
    and packet all filled in. The numbers are internally consistent and the
    final quantum is USD 38,400.00.
    """
    return VoyageState(
        voyage_id=voyage_id,
        perspective=perspective,
        stage="done",
        error=None,
        extraction=_extraction(),
        laytime=_laytime(),
        dispute=_dispute(perspective),
        packet=_packet(),
    )
