"""Bidirectional translation between the frozen Pydantic ``VoyageState`` tree and
the relational ORM rows in ``models``.

Exactness is the contract: ``orm_to_state(state_to_orm(s)) == s`` for any
VoyageState (the round-trip test guards this, and with it the EUR 84,375.00 gate).
Datetimes inside the tree are stored as ISO-8601 strings and handed back to
Pydantic verbatim, so the original timezone offset survives. ``created_at`` is a
real timestamp column, always UTC; SQLite returns it naive, so we reattach UTC.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..schemas import (
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
    SoFEvent,
    StatementOfFacts,
    VoyageState,
)
from . import models as m


def _ensure_utc(dt: datetime) -> datetime:
    """SQLite drops tzinfo; created_at is always UTC, so reattach it."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


# --- Pydantic -> ORM -------------------------------------------------------


def _charter_party_to_orm(cp: CharterParty) -> m.CharterPartyRow:
    return m.CharterPartyRow(
        form=cp.form,
        cp_date=cp.cp_date,
        vessel_name=cp.vessel_name,
        owner=cp.owner,
        charterer=cp.charterer,
        load_port=cp.load_port,
        discharge_port=cp.discharge_port,
        laytime_allowed_hours=cp.laytime_allowed_hours,
        laytime_basis=cp.laytime_basis,
        demurrage_rate_eur_per_day=cp.demurrage_rate_eur_per_day,
        despatch_rate_eur_per_day=cp.despatch_rate_eur_per_day,
        nor_tender_window=cp.nor_tender_window,
        laytime_commencement_rule=cp.laytime_commencement_rule,
        time_bar_days=cp.time_bar_days,
        time_bar_basis=cp.time_bar_basis,
        clause_excerpts=[
            m.ClauseExcerptRow(ord=i, clause_no=c.clause_no, text=c.text)
            for i, c in enumerate(cp.clause_excerpts)
        ],
        exception_clauses=[
            m.CpExceptionClauseRow(ord=i, value=v)
            for i, v in enumerate(cp.exception_clauses)
        ],
    )


def _extraction_to_orm(ext: ExtractionResult) -> m.Extraction:
    nor = ext.notice_of_readiness
    sof = ext.statement_of_facts
    return m.Extraction(
        charter_party=_charter_party_to_orm(ext.charter_party),
        notice_of_readiness=m.NoticeOfReadinessRow(
            tendered_at=_iso(nor.tendered_at),
            accepted_at=_iso(nor.accepted_at),
            tendered_by=nor.tendered_by,
            tendered_to=nor.tendered_to,
            location=nor.location,
            free_pratique_granted_at=_iso(nor.free_pratique_granted_at),
            berth_status_at_tender=nor.berth_status_at_tender,
        ),
        statement_of_facts=m.StatementOfFactsRow(
            port=sof.port,
            timezone=sof.timezone,
            events=[
                m.SoFEventRow(
                    ord=i,
                    event_id=e.id,
                    timestamp=_iso(e.timestamp),
                    description=e.description,
                    category=e.category,
                )
                for i, e in enumerate(sof.events)
            ],
        ),
    )


def _laytime_to_orm(lt: LaytimeResult) -> m.LaytimeResultRow:
    return m.LaytimeResultRow(
        laytime_allowed_hours=lt.laytime_allowed_hours,
        laytime_used_hours=lt.laytime_used_hours,
        time_on_demurrage_hours=lt.time_on_demurrage_hours,
        time_excepted_hours=lt.time_excepted_hours,
        demurrage_rate_per_hour_eur=lt.demurrage_rate_per_hour_eur,
        demurrage_due_eur=lt.demurrage_due_eur,
        despatch_due_eur=lt.despatch_due_eur,
        rows=[
            m.LaytimeRowRow(
                ord=i,
                from_ts=_iso(r.from_ts),
                to_ts=_iso(r.to_ts),
                duration_hours=r.duration_hours,
                counts=r.counts,
                status=r.status,
                reason=r.reason,
                running_total_hours=r.running_total_hours,
                event_id_start=r.event_id_start,
                event_id_end=r.event_id_end,
                contestable=r.contestable,
            )
            for i, r in enumerate(lt.rows)
        ],
        classifications=[
            m.EventClassificationRow(
                ord=i,
                event_id=c.event_id,
                counts_against_laytime=c.counts_against_laytime,
                applicable_exception=c.applicable_exception,
                clause_basis=c.clause_basis,
                reasoning=c.reasoning,
                contestable=c.contestable,
            )
            for i, c in enumerate(lt.classifications)
        ],
    )


def _dispute_to_orm(d: DisputeAnalysis) -> m.DisputeAnalysisRow:
    return m.DisputeAnalysisRow(
        perspective=d.perspective,
        overall_confidence=d.overall_confidence,
        narrative_paragraphs=[
            m.DisputeNarrativeParagraphRow(ord=i, text=p)
            for i, p in enumerate(d.narrative_paragraphs)
        ],
        flagged_events=[
            m.FlaggedEventRow(
                ord=i,
                event_id=fe.event_id,
                title=fe.title,
                summary=fe.summary,
                owner_argument=fe.owner_argument,
                charterer_argument=fe.charterer_argument,
                owner_position_strength=fe.owner_position_strength,
                incremental_demurrage_eur=fe.incremental_demurrage_eur,
                clauses_cited=[
                    m.FlaggedEventClauseRow(ord=j, value=v)
                    for j, v in enumerate(fe.clauses_cited)
                ],
                evidence_required=[
                    m.FlaggedEventEvidenceRow(ord=j, value=v)
                    for j, v in enumerate(fe.evidence_required)
                ],
            )
            for i, fe in enumerate(d.flagged_events)
        ],
    )


def _packet_to_orm(p: ClaimPacket) -> m.ClaimPacketRow:
    return m.ClaimPacketRow(
        quantum_eur=p.quantum_eur,
        executive_summary=p.executive_summary,
        dispute_narrative_markdown=p.dispute_narrative_markdown,
        claim_letter_markdown=p.claim_letter_markdown,
        time_bar_date=p.time_bar_date,
        submitted_within_time_bar=p.submitted_within_time_bar,
        days_until_time_bar=p.days_until_time_bar,
        supporting_documents=[
            m.ClaimPacketDocumentRow(ord=i, value=v)
            for i, v in enumerate(p.supporting_documents)
        ],
    )


def state_to_orm(state: VoyageState, owner_user_id: str | None = None) -> m.Voyage:
    voyage = m.Voyage(
        voyage_id=state.voyage_id,
        owner_user_id=owner_user_id,
        perspective=state.perspective,
        stage=state.stage,
        error=state.error,
        created_at=_ensure_utc(state.created_at),
    )
    if state.extraction is not None:
        voyage.extraction = _extraction_to_orm(state.extraction)
    if state.laytime is not None:
        voyage.laytime = _laytime_to_orm(state.laytime)
    if state.dispute is not None:
        voyage.dispute = _dispute_to_orm(state.dispute)
    if state.packet is not None:
        voyage.packet = _packet_to_orm(state.packet)
    return voyage


def update_orm_from_state(voyage: m.Voyage, state: VoyageState) -> None:
    """Update an existing Voyage row in place: scalar fields + the four analysis
    branches (replacing each via delete-orphan). Deliberately does NOT touch
    ``owner_user_id`` or ``documents`` — those are preserved across the staged
    pipeline saves/patches that rewrite the analysis tree."""
    voyage.perspective = state.perspective
    voyage.stage = state.stage
    voyage.error = state.error
    voyage.created_at = _ensure_utc(state.created_at)
    voyage.extraction = (
        _extraction_to_orm(state.extraction) if state.extraction is not None else None
    )
    voyage.laytime = (
        _laytime_to_orm(state.laytime) if state.laytime is not None else None
    )
    voyage.dispute = (
        _dispute_to_orm(state.dispute) if state.dispute is not None else None
    )
    voyage.packet = (
        _packet_to_orm(state.packet) if state.packet is not None else None
    )


# --- ORM -> Pydantic -------------------------------------------------------


def _extraction_from_orm(ext: m.Extraction) -> ExtractionResult:
    cp = ext.charter_party
    nor = ext.notice_of_readiness
    sof = ext.statement_of_facts
    return ExtractionResult(
        charter_party=CharterParty(
            form=cp.form,
            cp_date=cp.cp_date,
            vessel_name=cp.vessel_name,
            owner=cp.owner,
            charterer=cp.charterer,
            load_port=cp.load_port,
            discharge_port=cp.discharge_port,
            laytime_allowed_hours=cp.laytime_allowed_hours,
            laytime_basis=cp.laytime_basis,
            demurrage_rate_eur_per_day=cp.demurrage_rate_eur_per_day,
            despatch_rate_eur_per_day=cp.despatch_rate_eur_per_day,
            exception_clauses=[c.value for c in cp.exception_clauses],
            nor_tender_window=cp.nor_tender_window,
            laytime_commencement_rule=cp.laytime_commencement_rule,
            time_bar_days=cp.time_bar_days,
            time_bar_basis=cp.time_bar_basis,
            clause_excerpts=[
                ClauseExcerpt(clause_no=c.clause_no, text=c.text)
                for c in cp.clause_excerpts
            ],
        ),
        notice_of_readiness=NoticeOfReadiness(
            tendered_at=nor.tendered_at,
            accepted_at=nor.accepted_at,
            tendered_by=nor.tendered_by,
            tendered_to=nor.tendered_to,
            location=nor.location,
            free_pratique_granted_at=nor.free_pratique_granted_at,
            berth_status_at_tender=nor.berth_status_at_tender,
        ),
        statement_of_facts=StatementOfFacts(
            port=sof.port,
            timezone=sof.timezone,
            events=[
                SoFEvent(
                    id=e.event_id,
                    timestamp=e.timestamp,
                    description=e.description,
                    category=e.category,
                )
                for e in sof.events
            ],
        ),
    )


def _laytime_from_orm(lt: m.LaytimeResultRow) -> LaytimeResult:
    return LaytimeResult(
        laytime_allowed_hours=lt.laytime_allowed_hours,
        laytime_used_hours=lt.laytime_used_hours,
        time_on_demurrage_hours=lt.time_on_demurrage_hours,
        time_excepted_hours=lt.time_excepted_hours,
        demurrage_rate_per_hour_eur=lt.demurrage_rate_per_hour_eur,
        demurrage_due_eur=lt.demurrage_due_eur,
        despatch_due_eur=lt.despatch_due_eur,
        rows=[
            LaytimeRow(
                from_ts=r.from_ts,
                to_ts=r.to_ts,
                duration_hours=r.duration_hours,
                counts=r.counts,
                status=r.status,
                reason=r.reason,
                running_total_hours=r.running_total_hours,
                event_id_start=r.event_id_start,
                event_id_end=r.event_id_end,
                contestable=r.contestable,
            )
            for r in lt.rows
        ],
        classifications=[
            EventClassification(
                event_id=c.event_id,
                counts_against_laytime=c.counts_against_laytime,
                applicable_exception=c.applicable_exception,
                clause_basis=c.clause_basis,
                reasoning=c.reasoning,
                contestable=c.contestable,
            )
            for c in lt.classifications
        ],
    )


def _dispute_from_orm(d: m.DisputeAnalysisRow) -> DisputeAnalysis:
    return DisputeAnalysis(
        perspective=d.perspective,
        overall_confidence=d.overall_confidence,
        narrative_paragraphs=[p.text for p in d.narrative_paragraphs],
        flagged_events=[
            FlaggedEvent(
                event_id=fe.event_id,
                title=fe.title,
                summary=fe.summary,
                owner_argument=fe.owner_argument,
                charterer_argument=fe.charterer_argument,
                owner_position_strength=fe.owner_position_strength,
                incremental_demurrage_eur=fe.incremental_demurrage_eur,
                clauses_cited=[c.value for c in fe.clauses_cited],
                evidence_required=[e.value for e in fe.evidence_required],
            )
            for fe in d.flagged_events
        ],
    )


def _packet_from_orm(p: m.ClaimPacketRow) -> ClaimPacket:
    return ClaimPacket(
        quantum_eur=p.quantum_eur,
        executive_summary=p.executive_summary,
        dispute_narrative_markdown=p.dispute_narrative_markdown,
        claim_letter_markdown=p.claim_letter_markdown,
        supporting_documents=[d.value for d in p.supporting_documents],
        time_bar_date=p.time_bar_date,
        submitted_within_time_bar=p.submitted_within_time_bar,
        days_until_time_bar=p.days_until_time_bar,
    )


def orm_to_state(voyage: m.Voyage) -> VoyageState:
    return VoyageState(
        voyage_id=voyage.voyage_id,
        perspective=voyage.perspective,
        stage=voyage.stage,
        error=voyage.error,
        created_at=_ensure_utc(voyage.created_at),
        extraction=(
            _extraction_from_orm(voyage.extraction)
            if voyage.extraction is not None
            else None
        ),
        laytime=(
            _laytime_from_orm(voyage.laytime)
            if voyage.laytime is not None
            else None
        ),
        dispute=(
            _dispute_from_orm(voyage.dispute)
            if voyage.dispute is not None
            else None
        ),
        packet=(
            _packet_from_orm(voyage.packet)
            if voyage.packet is not None
            else None
        ),
    )
