"""Token-usage capture for admin observability.

Every Anthropic call funnels through ``agents.llm.extract_structured``; that one
site calls :func:`record` with the response's usage. We attach the triggering
``actor_sub`` / ``voyage_id`` from a ContextVar that the request or pipeline
sets (``contextvars`` are copied into ``asyncio.create_task``, so a background
pipeline inherits the value set by the route that launched it).

Per-key attribution: we never store the API key. :func:`key_fingerprint`
returns ``sha256(key)[:12]`` so usage can be grouped across the two rotating
keys; an optional ``ANTHROPIC_KEY_LABEL`` from Doppler gives each a human name.

Capture is best-effort: any failure is swallowed (logged at debug) so usage
accounting can never break a customer's pipeline run.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db.models import TokenUsageRow

logger = logging.getLogger("laytimely_api.usage")


@dataclass(frozen=True)
class _Context:
    actor_sub: Optional[str] = None
    voyage_id: Optional[str] = None


_CTX: contextvars.ContextVar[_Context] = contextvars.ContextVar(
    "usage_context", default=_Context()
)

# Bound once at app startup so this module can persist without importing main.
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def bind_sessionmaker(sm: async_sessionmaker[AsyncSession]) -> None:
    global _sessionmaker
    _sessionmaker = sm


def set_context(*, actor_sub: Optional[str], voyage_id: Optional[str]) -> None:
    """Set the attribution context for the current execution context. Use this
    before ``asyncio.create_task`` so the spawned task inherits the value."""
    _CTX.set(_Context(actor_sub=actor_sub, voyage_id=voyage_id))


@contextlib.contextmanager
def context(*, actor_sub: Optional[str], voyage_id: Optional[str]) -> Iterator[None]:
    """Scope attribution to a synchronous block (revise/rebut/citations routes)."""
    token = _CTX.set(_Context(actor_sub=actor_sub, voyage_id=voyage_id))
    try:
        yield
    finally:
        _CTX.reset(token)


@lru_cache(maxsize=4)
def _fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def key_fingerprint() -> Optional[str]:
    key = os.environ.get("ANTHROPIC_API_KEY") or ""
    return _fingerprint(key) if key else None


def key_label() -> Optional[str]:
    return os.environ.get("ANTHROPIC_KEY_LABEL") or None


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


async def record(usage: Any, *, model: str, feature: str) -> None:
    """Persist one usage row. ``usage`` is the SDK response usage object
    (input_tokens / output_tokens / cache_* ). Best-effort: never raises."""
    if _sessionmaker is None:
        return
    try:
        ctx = _CTX.get()
        row = TokenUsageRow(
            actor_sub=ctx.actor_sub,
            voyage_id=ctx.voyage_id,
            feature=feature,
            model=model,
            input_tokens=_as_int(getattr(usage, "input_tokens", 0)),
            output_tokens=_as_int(getattr(usage, "output_tokens", 0)),
            cache_read_tokens=_as_int(
                getattr(usage, "cache_read_input_tokens", 0)
            ),
            cache_creation_tokens=_as_int(
                getattr(usage, "cache_creation_input_tokens", 0)
            ),
            key_fp=key_fingerprint(),
            key_label=key_label(),
        )
        async with _sessionmaker() as session:
            session.add(row)
            await session.commit()
    except Exception:  # noqa: BLE001 — usage logging must never break a run
        logger.debug("token usage capture failed", exc_info=True)
