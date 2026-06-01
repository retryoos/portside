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
    # Real-auth credential fields (added with the multi-user auth work). Both
    # are nullable so pre-existing seed/dev rows (which never had a password)
    # keep validating; only accounts created via /auth/signup carry a hash.
    # ``email_lower`` is the case-folded unique key used for login + dup checks;
    # ``email`` keeps the original casing for display.
    email_lower: Mapped[str | None] = mapped_column(
        String, nullable=True, unique=True, index=True
    )
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# --- workspaces (W7/§2.1) --------------------------------------------------


class WorkspaceRow(Base):
    """A team workspace. Each user has at least one (their personal
    workspace, named after them, created lazily on first auth). Real teams
    add more members via invitations.

    Voyages, audit events, and email-in addresses are workspace-scoped once
    the WORKSPACES_UI feature flag is on; until then everything routes to
    the caller's personal workspace by default.
    """

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    plan: Mapped[str] = mapped_column(String, default="self_serve")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


class MembershipRow(Base):
    """One user's role within one workspace.

    Roles (closed vocabulary): owner / admin / member. Enforced at the route
    boundary by ``require_workspace_role(min_role)``.
    """

    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    user_sub: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


class InvitationRow(Base):
    """Pending workspace invitation by email.

    ``token`` is a URL-safe random string; the invite URL is
    ``https://laytimely.com/invite/<token>``. ``expires_at`` is enforced at
    the accept route.
    """

    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    invited_by_sub: Mapped[str] = mapped_column(String)
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    accepted_by_sub: Mapped[str | None] = mapped_column(String, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    # Uploaded source PDFs (A3). Kept off the content-rewrite path: save/patch
    # only replace the four analysis branches, never the documents.
    documents: Mapped[list[VoyageDocumentRow]] = relationship(
        back_populates="voyage",
        order_by="VoyageDocumentRow.role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # External evidence gathered by the researcher (A7). Also off the rewrite
    # path: gathered once, persisted, and returned on subsequent reads.
    evidence: Mapped[list[VoyageEvidenceRow]] = relationship(
        back_populates="voyage",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Analyst legal citations cached per (voyage, event). Same first-read-then-
    # cache shape as ``evidence``; populated by the /citations route which
    # invokes the per-event picker pass over the curated corpus.
    citations: Mapped[list["VoyageCitationRow"]] = relationship(
        back_populates="voyage",
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


# --- uploaded source PDFs (A3) ---------------------------------------------


class VoyageDocumentRow(Base):
    __tablename__ = "voyage_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[str] = mapped_column(
        ForeignKey("voyages.voyage_id", ondelete="CASCADE"), index=True
    )
    voyage: Mapped[Voyage] = relationship(back_populates="documents")
    role: Mapped[str] = mapped_column(String)
    object_key: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# --- gathered external evidence (A7) ---------------------------------------


class VoyageEvidenceRow(Base):
    __tablename__ = "voyage_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[str] = mapped_column(
        ForeignKey("voyages.voyage_id", ondelete="CASCADE"), index=True
    )
    voyage: Mapped[Voyage] = relationship(back_populates="evidence")
    event_id: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    observed_value: Mapped[str] = mapped_column(String)
    supports: Mapped[str] = mapped_column(String)
    citation: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# --- analyst citations (W5/§1.6) -------------------------------------------


class VoyageCitationRow(Base):
    """One verified CitedAuthority cached per (voyage, event).

    The analyst citation pass (analyst.run_with_citations) runs against the
    case-law corpus + (future) IMO/EUR-Lex tool surfaces. The picker output
    is validated against the candidate list so case_id is always real; we
    cache the surviving rows so the second read does not re-call the model.
    """

    __tablename__ = "voyage_citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[str] = mapped_column(
        ForeignKey("voyages.voyage_id", ondelete="CASCADE"), index=True
    )
    voyage: Mapped[Voyage] = relationship(back_populates="citations")
    event_id: Mapped[str] = mapped_column(String, index=True)
    citation: Mapped[str] = mapped_column(Text)
    tool_used: Mapped[str] = mapped_column(String)
    proposition: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )


# --- audit log (W7/§2.2) ---------------------------------------------------


class AuditEventRow(Base):
    """Append-only record of every state-mutating action.

    Population is explicit: every mutation route calls ``audit.record(...)``
    rather than relying on a decorator (decorators hide what got written).
    ``payload_redacted`` is a small JSON blob whose schema is per-action;
    PII and the model's prose are intentionally NOT included. See
    ``laytimely_api/audit.py`` for the helper and the action vocabulary.

    Retention: 90 days hot in Postgres; the CloudWatch sink for the long tail
    lands in the observability work (Tier 2 of the customer checklist).
    """

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_sub: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    target_type: Mapped[str] = mapped_column(String, index=True)
    target_id: Mapped[str] = mapped_column(String, index=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    # Per-action payload, redacted at the call site. Stored as a string so it
    # round-trips across SQLite (no JSON column) and Postgres (could promote
    # to JSONB in a follow-up; the helper writes JSON-encoded strings either
    # way so the call sites do not change).
    payload_redacted: Mapped[str] = mapped_column(Text, default="{}")


# --- token usage (admin observability) -------------------------------------


class TokenUsageRow(Base):
    """One Anthropic call's token usage, captured at the single LLM chokepoint
    (``agents.llm.extract_structured``) so the admin dashboard can aggregate
    spend by user, feature, model, and API key.

    ``actor_sub`` / ``voyage_id`` come from a ContextVar set by the request or
    pipeline that triggered the call. ``feature`` is the structured output
    model name (e.g. ``ExtractionResult``), a free per-stage label. ``key_fp``
    is a non-reversible fingerprint of the active API key (sha256 prefix), so
    usage can be attributed across the two rotating keys without ever storing
    the key itself; ``key_label`` is an optional human name from Doppler.
    """

    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    actor_sub: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    voyage_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    feature: Mapped[str] = mapped_column(String, index=True)
    model: Mapped[str] = mapped_column(String, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0)
    key_fp: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    key_label: Mapped[str | None] = mapped_column(String, nullable=True)
