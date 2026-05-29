"""SQLAlchemy ORM mapping of the full VoyageState tree.

The Pydantic contract in ``schemas.py`` is FROZEN and stays the integration
surface; these ORM models are an internal, fully-relational persistence of that
tree (one table per model, child tables for every list, an ``ord`` column so
ordered lists round-trip exactly). The bidirectional translation lives in
``db/mapping.py``.

Datetime storage:
  * ``voyages.created_at`` is a real timestamp column (sortable for the dashboard
    list) and is always UTC.
  * Every other datetime (NOR, SoF events, laytime rows) is stored as its
    ISO-8601 *string* so the original timezone offset round-trips byte-for-byte
    (SQLite has no native tz; the demo data mixes UTC and +02:00). The mapping
    layer hands these strings straight back to Pydantic, which re-parses them.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# --- ownership -------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# --- top-level voyage ------------------------------------------------------


class Voyage(Base):
    __tablename__ = "voyages"

    voyage_id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    perspective: Mapped[str] = mapped_column(String)
    stage: Mapped[str] = mapped_column(String)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    extraction: Mapped[Extraction | None] = relationship(
        back_populates="voyage",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    laytime: Mapped[LaytimeResultRow | None] = relationship(
        back_populates="voyage",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    dispute: Mapped[DisputeAnalysisRow | None] = relationship(
        back_populates="voyage",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    packet: Mapped[ClaimPacketRow | None] = relationship(
        back_populates="voyage",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# --- extraction branch -----------------------------------------------------


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[str] = mapped_column(
        ForeignKey("voyages.voyage_id", ondelete="CASCADE"), unique=True, index=True
    )
    voyage: Mapped[Voyage] = relationship(back_populates="extraction")

    charter_party: Mapped[CharterPartyRow] = relationship(
        back_populates="extraction",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notice_of_readiness: Mapped[NoticeOfReadinessRow] = relationship(
        back_populates="extraction",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    statement_of_facts: Mapped[StatementOfFactsRow] = relationship(
        back_populates="extraction",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CharterPartyRow(Base):
    __tablename__ = "charter_parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extraction_id: Mapped[int] = mapped_column(
        ForeignKey("extractions.id", ondelete="CASCADE"), unique=True, index=True
    )
    extraction: Mapped[Extraction] = relationship(back_populates="charter_party")

    form: Mapped[str] = mapped_column(String)
    cp_date: Mapped[str] = mapped_column(String)
    vessel_name: Mapped[str] = mapped_column(String)
    owner: Mapped[str] = mapped_column(String)
    charterer: Mapped[str] = mapped_column(String)
    load_port: Mapped[str] = mapped_column(String)
    discharge_port: Mapped[str] = mapped_column(String)
    laytime_allowed_hours: Mapped[float] = mapped_column(Float)
    laytime_basis: Mapped[str] = mapped_column(String)
    demurrage_rate_eur_per_day: Mapped[float] = mapped_column(Float)
    despatch_rate_eur_per_day: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    nor_tender_window: Mapped[str] = mapped_column(Text)
    laytime_commencement_rule: Mapped[str] = mapped_column(Text)
    time_bar_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_bar_basis: Mapped[str] = mapped_column(String)

    clause_excerpts: Mapped[list[ClauseExcerptRow]] = relationship(
        back_populates="charter_party",
        order_by="ClauseExcerptRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    exception_clauses: Mapped[list[CpExceptionClauseRow]] = relationship(
        back_populates="charter_party",
        order_by="CpExceptionClauseRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ClauseExcerptRow(Base):
    __tablename__ = "clause_excerpts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    charter_party_id: Mapped[int] = mapped_column(
        ForeignKey("charter_parties.id", ondelete="CASCADE"), index=True
    )
    charter_party: Mapped[CharterPartyRow] = relationship(
        back_populates="clause_excerpts"
    )
    ord: Mapped[int] = mapped_column(Integer)
    clause_no: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)


class CpExceptionClauseRow(Base):
    __tablename__ = "cp_exception_clauses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    charter_party_id: Mapped[int] = mapped_column(
        ForeignKey("charter_parties.id", ondelete="CASCADE"), index=True
    )
    charter_party: Mapped[CharterPartyRow] = relationship(
        back_populates="exception_clauses"
    )
    ord: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(String)


class NoticeOfReadinessRow(Base):
    __tablename__ = "notices_of_readiness"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extraction_id: Mapped[int] = mapped_column(
        ForeignKey("extractions.id", ondelete="CASCADE"), unique=True, index=True
    )
    extraction: Mapped[Extraction] = relationship(
        back_populates="notice_of_readiness"
    )

    tendered_at: Mapped[str] = mapped_column(String)
    accepted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    tendered_by: Mapped[str] = mapped_column(String)
    tendered_to: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    free_pratique_granted_at: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    berth_status_at_tender: Mapped[str | None] = mapped_column(String, nullable=True)


class StatementOfFactsRow(Base):
    __tablename__ = "statements_of_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extraction_id: Mapped[int] = mapped_column(
        ForeignKey("extractions.id", ondelete="CASCADE"), unique=True, index=True
    )
    extraction: Mapped[Extraction] = relationship(
        back_populates="statement_of_facts"
    )
    port: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String)

    events: Mapped[list[SoFEventRow]] = relationship(
        back_populates="statement_of_facts",
        order_by="SoFEventRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SoFEventRow(Base):
    __tablename__ = "sof_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sof_id: Mapped[int] = mapped_column(
        ForeignKey("statements_of_facts.id", ondelete="CASCADE"), index=True
    )
    statement_of_facts: Mapped[StatementOfFactsRow] = relationship(
        back_populates="events"
    )
    ord: Mapped[int] = mapped_column(Integer)
    event_id: Mapped[str] = mapped_column(String)
    timestamp: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String)


# --- laytime branch --------------------------------------------------------


class LaytimeResultRow(Base):
    __tablename__ = "laytime_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[str] = mapped_column(
        ForeignKey("voyages.voyage_id", ondelete="CASCADE"), unique=True, index=True
    )
    voyage: Mapped[Voyage] = relationship(back_populates="laytime")

    laytime_allowed_hours: Mapped[float] = mapped_column(Float)
    laytime_used_hours: Mapped[float] = mapped_column(Float)
    time_on_demurrage_hours: Mapped[float] = mapped_column(Float)
    time_excepted_hours: Mapped[float] = mapped_column(Float)
    demurrage_rate_per_hour_eur: Mapped[float] = mapped_column(Float)
    demurrage_due_eur: Mapped[float] = mapped_column(Float)
    despatch_due_eur: Mapped[float | None] = mapped_column(Float, nullable=True)

    rows: Mapped[list[LaytimeRowRow]] = relationship(
        back_populates="laytime_result",
        order_by="LaytimeRowRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    classifications: Mapped[list[EventClassificationRow]] = relationship(
        back_populates="laytime_result",
        order_by="EventClassificationRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LaytimeRowRow(Base):
    __tablename__ = "laytime_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    laytime_result_id: Mapped[int] = mapped_column(
        ForeignKey("laytime_results.id", ondelete="CASCADE"), index=True
    )
    laytime_result: Mapped[LaytimeResultRow] = relationship(back_populates="rows")
    ord: Mapped[int] = mapped_column(Integer)

    from_ts: Mapped[str] = mapped_column(String)
    to_ts: Mapped[str] = mapped_column(String)
    duration_hours: Mapped[float] = mapped_column(Float)
    counts: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    running_total_hours: Mapped[float] = mapped_column(Float)
    event_id_start: Mapped[str] = mapped_column(String)
    event_id_end: Mapped[str] = mapped_column(String)
    contestable: Mapped[bool] = mapped_column(Boolean)


class EventClassificationRow(Base):
    __tablename__ = "event_classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    laytime_result_id: Mapped[int] = mapped_column(
        ForeignKey("laytime_results.id", ondelete="CASCADE"), index=True
    )
    laytime_result: Mapped[LaytimeResultRow] = relationship(
        back_populates="classifications"
    )
    ord: Mapped[int] = mapped_column(Integer)

    event_id: Mapped[str] = mapped_column(String)
    counts_against_laytime: Mapped[bool] = mapped_column(Boolean)
    applicable_exception: Mapped[str | None] = mapped_column(String, nullable=True)
    clause_basis: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str] = mapped_column(Text)
    contestable: Mapped[bool] = mapped_column(Boolean)


# --- dispute branch --------------------------------------------------------


class DisputeAnalysisRow(Base):
    __tablename__ = "dispute_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[str] = mapped_column(
        ForeignKey("voyages.voyage_id", ondelete="CASCADE"), unique=True, index=True
    )
    voyage: Mapped[Voyage] = relationship(back_populates="dispute")

    perspective: Mapped[str] = mapped_column(String)
    overall_confidence: Mapped[float] = mapped_column(Float)

    narrative_paragraphs: Mapped[list[DisputeNarrativeParagraphRow]] = relationship(
        back_populates="dispute",
        order_by="DisputeNarrativeParagraphRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    flagged_events: Mapped[list[FlaggedEventRow]] = relationship(
        back_populates="dispute",
        order_by="FlaggedEventRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DisputeNarrativeParagraphRow(Base):
    __tablename__ = "dispute_narrative_paragraphs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dispute_id: Mapped[int] = mapped_column(
        ForeignKey("dispute_analyses.id", ondelete="CASCADE"), index=True
    )
    dispute: Mapped[DisputeAnalysisRow] = relationship(
        back_populates="narrative_paragraphs"
    )
    ord: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)


class FlaggedEventRow(Base):
    __tablename__ = "flagged_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dispute_id: Mapped[int] = mapped_column(
        ForeignKey("dispute_analyses.id", ondelete="CASCADE"), index=True
    )
    dispute: Mapped[DisputeAnalysisRow] = relationship(
        back_populates="flagged_events"
    )
    ord: Mapped[int] = mapped_column(Integer)

    event_id: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    owner_argument: Mapped[str] = mapped_column(Text)
    charterer_argument: Mapped[str] = mapped_column(Text)
    owner_position_strength: Mapped[float] = mapped_column(Float)
    incremental_demurrage_eur: Mapped[float] = mapped_column(Float)

    clauses_cited: Mapped[list[FlaggedEventClauseRow]] = relationship(
        back_populates="flagged_event",
        order_by="FlaggedEventClauseRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    evidence_required: Mapped[list[FlaggedEventEvidenceRow]] = relationship(
        back_populates="flagged_event",
        order_by="FlaggedEventEvidenceRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FlaggedEventClauseRow(Base):
    __tablename__ = "flagged_event_clauses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flagged_event_id: Mapped[int] = mapped_column(
        ForeignKey("flagged_events.id", ondelete="CASCADE"), index=True
    )
    flagged_event: Mapped[FlaggedEventRow] = relationship(
        back_populates="clauses_cited"
    )
    ord: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(String)


class FlaggedEventEvidenceRow(Base):
    __tablename__ = "flagged_event_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flagged_event_id: Mapped[int] = mapped_column(
        ForeignKey("flagged_events.id", ondelete="CASCADE"), index=True
    )
    flagged_event: Mapped[FlaggedEventRow] = relationship(
        back_populates="evidence_required"
    )
    ord: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(Text)


# --- packet branch ---------------------------------------------------------


class ClaimPacketRow(Base):
    __tablename__ = "claim_packets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[str] = mapped_column(
        ForeignKey("voyages.voyage_id", ondelete="CASCADE"), unique=True, index=True
    )
    voyage: Mapped[Voyage] = relationship(back_populates="packet")

    quantum_eur: Mapped[float] = mapped_column(Float)
    executive_summary: Mapped[str] = mapped_column(Text)
    dispute_narrative_markdown: Mapped[str] = mapped_column(Text)
    claim_letter_markdown: Mapped[str] = mapped_column(Text)
    time_bar_date: Mapped[str] = mapped_column(String)
    submitted_within_time_bar: Mapped[bool] = mapped_column(Boolean)
    days_until_time_bar: Mapped[int] = mapped_column(Integer)

    supporting_documents: Mapped[list[ClaimPacketDocumentRow]] = relationship(
        back_populates="packet",
        order_by="ClaimPacketDocumentRow.ord",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ClaimPacketDocumentRow(Base):
    __tablename__ = "claim_packet_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    packet_id: Mapped[int] = mapped_column(
        ForeignKey("claim_packets.id", ondelete="CASCADE"), index=True
    )
    packet: Mapped[ClaimPacketRow] = relationship(
        back_populates="supporting_documents"
    )
    ord: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(Text)
