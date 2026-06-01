"""Audit log (notes/architecture_weeks_5_to_8.md §2.2).

Every state mutation writes one row. Calls are explicit (no decorator) so a
code-review reader sees what gets logged. The action vocabulary is a closed
``Literal`` set; adding a new action is a single-line code change that
travels with the route it audits.

Payloads are *redacted* at the call site: include only the minimum primitive
fields the audit reader needs (recipient list, voyage perspective, stage
transition, etc.). Never include free-text claim prose, never include PDFs,
never include email body. The model's output is not audit material.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable, Literal, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from pydantic import BaseModel

from .db.models import AuditEventRow

logger = logging.getLogger("laytimely_api.audit")

# Closed action vocabulary. Every site that calls ``record`` must pass one of
# these literals. New actions are added with the route that emits them; the
# closed set prevents drift.
AuditAction = Literal[
    "voyage.create",
    "voyage.delete",
    "voyage.status_change",
    "voyage.revise_apply",
    "voyage.rebuttal",
    "voyage.letter_email",
    "voyage.evidence_refresh",
    "voyage.from_email",
    "workspace.create",
    "workspace.invite",
    "workspace.accept",
    "workspace.member_remove",
    # Auth + admin events (admin observability).
    "auth.signup",
    "auth.login",
    "auth.login_failed",
    "auth.demo",
    "admin.view",
]

# Closed target taxonomy.
AuditTarget = Literal[
    "voyage", "claim", "workspace", "membership", "invitation", "user", "admin"
]


class AuditEvent(BaseModel):
    """Read projection of an audit row."""

    id: int
    actor_sub: Optional[str]
    action: str
    target_type: str
    target_id: str
    at: str  # ISO-8601
    payload: dict[str, Any]


async def record(
    session: AsyncSession,
    *,
    actor_sub: Optional[str],
    action: AuditAction,
    target_type: AuditTarget,
    target_id: str,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    """Append one audit row.

    The caller's session is reused so the audit insert participates in the
    same transaction as the mutation it records, which is the point of
    having an audit log at all. If the mutation rolls back, the audit row
    rolls back with it; we never log a phantom success.
    """
    body = _redact(payload or {})
    row = AuditEventRow(
        actor_sub=actor_sub,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload_redacted=json.dumps(body, sort_keys=True, separators=(",", ":")),
    )
    session.add(row)
    await session.flush()
    logger.info(
        "audit %s %s/%s actor=%s payload=%s",
        action,
        target_type,
        target_id,
        actor_sub or "?",
        body,
    )


# ---------------------------------------------------------------------------
# Convenience reader for the admin "/audit" route
# ---------------------------------------------------------------------------


async def reap_older_than(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    retention_days: int,
) -> int:
    """Delete audit rows older than ``retention_days``.

    Called from the FastAPI lifespan on startup so a long-running process
    keeps the table bounded without an external cron. The hot table for
    incident response is the last 90 days; everything beyond that is in
    CloudWatch (planned). 0 disables retention.
    """
    if retention_days <= 0:
        return 0
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    async with sessionmaker() as session:
        async with session.begin():
            from sqlalchemy import delete as _delete
            result = await session.execute(
                _delete(AuditEventRow).where(AuditEventRow.at < cutoff)
            )
    return result.rowcount or 0


# The Anthropic-calling ("spend") actions. The per-account and global quotas
# count rows with these actions in a rolling window to bound model cost. Adding
# a new model-calling route means adding its action here so it counts.
COST_ACTIONS: tuple[str, ...] = (
    "voyage.create",
    "voyage.revise_apply",
    "voyage.rebuttal",
    "voyage.evidence_refresh",
    "voyage.from_email",
)


async def count_actions_since(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    actions: tuple[str, ...],
    since: "datetime",
    actor_sub: str | None = None,
) -> int:
    """Count audit rows with one of ``actions`` recorded at/after ``since``.

    When ``actor_sub`` is given the count is scoped to that account (the
    per-account quota); when None it counts every account (the global daily
    budget cap). One cheap indexed COUNT; both ``action`` and ``at`` are
    indexed columns.
    """
    from sqlalchemy import func

    stmt = (
        select(func.count())
        .select_from(AuditEventRow)
        .where(AuditEventRow.action.in_(actions), AuditEventRow.at >= since)
    )
    if actor_sub is not None:
        stmt = stmt.where(AuditEventRow.actor_sub == actor_sub)
    async with sessionmaker() as session:
        return int((await session.execute(stmt)).scalar_one())


async def list_for_actor(
    sessionmaker: async_sessionmaker[AsyncSession],
    actor_sub: str,
    *,
    limit: int = 100,
) -> list[AuditEvent]:
    """Most-recent-first list of the caller's own audit events. Used by
    ``GET /audit``. Admin / workspace views land later with the workspace
    work (§2.1)."""
    async with sessionmaker() as session:
        result = await session.execute(
            select(AuditEventRow)
            .where(AuditEventRow.actor_sub == actor_sub)
            .order_by(desc(AuditEventRow.at))
            .limit(limit)
        )
        rows = result.scalars().all()
    return [_to_pydantic(r) for r in rows]


def _to_pydantic(row: AuditEventRow) -> AuditEvent:
    try:
        payload = json.loads(row.payload_redacted or "{}")
    except json.JSONDecodeError:
        payload = {}
    return AuditEvent(
        id=row.id,
        actor_sub=row.actor_sub,
        action=row.action,
        target_type=row.target_type,
        target_id=row.target_id,
        at=row.at.isoformat(),
        payload=payload,
    )


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

# Keys whose values are kept as-is. Anything not on the allowlist becomes a
# count-or-marker so we never accidentally log a model-emitted string body.
_PRIMITIVE_KEYS = {
    "perspective",
    "stage",
    "from_stage",
    "to_stage",
    "voyage_id",
    "vessel",
    "workspace_id",
    "role",
    "code",
    "sandbox",
    "ses_message_id",
    "recipients_to",
    "recipients_cc",
    "recipients_bcc",
    "evidence_event_id",
    "source",
    "tier",
    "action",
}


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop or coerce anything outside the primitive allowlist.

    The rule: numbers, booleans, ISO-style strings, and short identifiers
    pass through; long strings become ``"<len:N>"`` so the audit reader can
    see "something was here" without leaking the content.
    """
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in _PRIMITIVE_KEYS:
            safe[key] = _summarise(value)
            continue
        if isinstance(value, (bool, int, float)) or value is None:
            safe[key] = value
        elif isinstance(value, str):
            safe[key] = value if len(value) <= 120 else f"<len:{len(value)}>"
        elif isinstance(value, Iterable):
            seq = list(value)
            if all(isinstance(s, str) for s in seq):
                safe[key] = [s if len(s) <= 80 else f"<len:{len(s)}>" for s in seq]
            else:
                safe[key] = f"<list:{len(seq)}>"
        else:
            safe[key] = f"<{type(value).__name__}>"
    return safe


def _summarise(value: Any) -> Any:
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, str):
        return f"<len:{len(value)}>" if len(value) > 40 else value
    if isinstance(value, Iterable):
        seq = list(value)
        return f"<list:{len(seq)}>"
    return f"<{type(value).__name__}>"
