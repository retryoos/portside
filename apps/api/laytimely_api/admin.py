"""Admin observability aggregates (token usage + auth events).

Read-only rollups over ``token_usage`` and the auth rows of ``audit_events``,
for the gated /admin dashboard. Aggregation is done in Python over a bounded
time window (early-stage volumes are small and this stays DB-agnostic across
SQLite/Postgres). Cost is an estimate from public per-model token prices; the
Anthropic Console remains the billing source of truth.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db.models import AuditEventRow, TokenUsageRow, User

# USD per 1,000,000 tokens (input, output). Matched by substring so model id
# variants resolve; unknown models fall back to Sonnet pricing.
_PRICES: dict[str, tuple[float, float]] = {
    "opus": (15.0, 75.0),
    "haiku": (0.80, 4.0),
    "sonnet": (3.0, 15.0),
}


def _price(model: str) -> tuple[float, float]:
    m = (model or "").lower()
    for key, prices in _PRICES.items():
        if key in m:
            return prices
    return _PRICES["sonnet"]


def est_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    in_price, out_price = _price(model)
    return round(
        input_tokens / 1_000_000 * in_price
        + output_tokens / 1_000_000 * out_price,
        4,
    )


_AUTH_ACTIONS = ("auth.signup", "auth.login", "auth.login_failed", "auth.demo")


# ---------------------------------------------------------------------------
# Wire models
# ---------------------------------------------------------------------------


class UsageBucket(BaseModel):
    key: str  # the group value (model / feature / key label / user)
    label: str | None = None  # human label where the key is opaque
    calls: int
    input_tokens: int
    output_tokens: int
    est_cost_usd: float


class TimePoint(BaseModel):
    date: str  # YYYY-MM-DD
    calls: int
    input_tokens: int
    output_tokens: int
    est_cost_usd: float


class AuthEvent(BaseModel):
    at: str
    action: str
    actor_sub: str | None
    email: str | None
    target_id: str


class AdminOverview(BaseModel):
    window_days: int
    signups: int
    logins: int
    login_failures: int
    demo_starts: int
    active_users: int
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    est_cost_usd: float
    by_key: list[UsageBucket]
    by_model: list[UsageBucket]
    by_feature: list[UsageBucket]
    top_users: list[UsageBucket]
    timeseries: list[TimePoint]


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


async def _emails_for(session: AsyncSession, subs: set[str]) -> dict[str, str]:
    subs = {s for s in subs if s}
    if not subs:
        return {}
    rows = (
        await session.execute(select(User.id, User.email).where(User.id.in_(subs)))
    ).all()
    return {sid: (email or "") for sid, email in rows}


def _bucket(rows: list[TokenUsageRow], keyfn, labelfn=None) -> list[UsageBucket]:
    agg: dict[str, dict] = defaultdict(
        lambda: {"calls": 0, "in": 0, "out": 0, "cost": 0.0, "label": None}
    )
    for r in rows:
        k = keyfn(r) or "unknown"
        a = agg[k]
        a["calls"] += 1
        a["in"] += r.input_tokens
        a["out"] += r.output_tokens
        a["cost"] += est_cost(r.model, r.input_tokens, r.output_tokens)
        if labelfn and a["label"] is None:
            a["label"] = labelfn(r)
    out = [
        UsageBucket(
            key=k,
            label=v["label"],
            calls=v["calls"],
            input_tokens=v["in"],
            output_tokens=v["out"],
            est_cost_usd=round(v["cost"], 4),
        )
        for k, v in agg.items()
    ]
    out.sort(key=lambda b: b.est_cost_usd, reverse=True)
    return out


async def overview(
    sessionmaker: async_sessionmaker[AsyncSession], *, days: int = 30
) -> AdminOverview:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_naive = since.replace(tzinfo=None)
    async with sessionmaker() as session:
        usage_rows = list(
            (
                await session.execute(
                    select(TokenUsageRow).where(TokenUsageRow.at >= since_naive)
                )
            )
            .scalars()
            .all()
        )
        auth_rows = list(
            (
                await session.execute(
                    select(AuditEventRow).where(
                        AuditEventRow.action.in_(_AUTH_ACTIONS),
                        AuditEventRow.at >= since_naive,
                    )
                )
            )
            .scalars()
            .all()
        )
        user_subs = {r.actor_sub for r in usage_rows if r.actor_sub} | {
            r.actor_sub for r in auth_rows if r.actor_sub
        }
        emails = await _emails_for(session, user_subs)

    counts = defaultdict(int)
    for r in auth_rows:
        counts[r.action] += 1

    by_user = _bucket(
        usage_rows,
        keyfn=lambda r: r.actor_sub,
        labelfn=lambda r: emails.get(r.actor_sub or "", None),
    )[:10]

    # Daily timeseries.
    days_agg: dict[str, dict] = defaultdict(
        lambda: {"calls": 0, "in": 0, "out": 0, "cost": 0.0}
    )
    for r in usage_rows:
        d = r.at.date().isoformat()
        a = days_agg[d]
        a["calls"] += 1
        a["in"] += r.input_tokens
        a["out"] += r.output_tokens
        a["cost"] += est_cost(r.model, r.input_tokens, r.output_tokens)
    timeseries = [
        TimePoint(
            date=d,
            calls=v["calls"],
            input_tokens=v["in"],
            output_tokens=v["out"],
            est_cost_usd=round(v["cost"], 4),
        )
        for d, v in sorted(days_agg.items())
    ]

    total_in = sum(r.input_tokens for r in usage_rows)
    total_out = sum(r.output_tokens for r in usage_rows)
    total_cost = round(
        sum(est_cost(r.model, r.input_tokens, r.output_tokens) for r in usage_rows),
        4,
    )
    active = len({r.actor_sub for r in usage_rows if r.actor_sub})

    return AdminOverview(
        window_days=days,
        signups=counts["auth.signup"],
        logins=counts["auth.login"],
        login_failures=counts["auth.login_failed"],
        demo_starts=counts["auth.demo"],
        active_users=active,
        total_calls=len(usage_rows),
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        est_cost_usd=total_cost,
        by_key=_bucket(
            usage_rows,
            keyfn=lambda r: r.key_label or r.key_fp,
            labelfn=lambda r: r.key_label,
        ),
        by_model=_bucket(usage_rows, keyfn=lambda r: r.model),
        by_feature=_bucket(usage_rows, keyfn=lambda r: r.feature),
        top_users=by_user,
        timeseries=timeseries,
    )


async def recent_auth_events(
    sessionmaker: async_sessionmaker[AsyncSession], *, limit: int = 50
) -> list[AuthEvent]:
    async with sessionmaker() as session:
        rows = list(
            (
                await session.execute(
                    select(AuditEventRow)
                    .where(AuditEventRow.action.in_(_AUTH_ACTIONS))
                    .order_by(AuditEventRow.at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        emails = await _emails_for(session, {r.actor_sub for r in rows if r.actor_sub})
    return [
        AuthEvent(
            at=r.at.isoformat(),
            action=r.action,
            actor_sub=r.actor_sub,
            email=emails.get(r.actor_sub or "", None),
            target_id=r.target_id,
        )
        for r in rows
    ]
