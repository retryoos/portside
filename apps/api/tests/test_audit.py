"""Tests for the audit log (notes/architecture_weeks_5_to_8.md §2.2).

Three blocks:

- ``record`` writes one row per call with the right action, target, actor,
  and a JSON-encoded payload.
- ``_redact`` drops anything outside the primitive allowlist and coerces
  long strings to a length marker (no model prose ever lands in the log).
- ``list_for_actor`` returns the caller's events newest first, capped at
  the requested limit.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from portside_api import audit  # noqa: E402
from portside_api.audit import _redact  # noqa: E402
from portside_api.db.engine import create_all, make_engine, make_sessionmaker  # noqa: E402


@pytest.fixture
def sessionmaker(tmp_path: Path):
    """Per-test SQLite DB so each test starts clean.

    Async fixtures need an event loop wrapper to construct the schema; we use
    asyncio.run because pytest-asyncio is not in the dev deps and the rest of
    the suite already uses this pattern.
    """
    url = f"sqlite+aiosqlite:///{tmp_path / 'audit.db'}"
    engine = make_engine(url)
    asyncio.run(create_all(engine))
    sm = make_sessionmaker(engine)
    yield sm
    asyncio.run(engine.dispose())


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------


def test_record_writes_one_row_with_the_expected_fields(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            await audit.record(
                s,
                actor_sub="user-1",
                action="voyage.create",
                target_type="voyage",
                target_id="v_abc",
                payload={"perspective": "owner"},
            )
            await s.commit()
        events = await audit.list_for_actor(sessionmaker, "user-1")
        return events

    events = asyncio.run(go())
    assert len(events) == 1
    e = events[0]
    assert e.action == "voyage.create"
    assert e.target_type == "voyage"
    assert e.target_id == "v_abc"
    assert e.actor_sub == "user-1"
    assert e.payload == {"perspective": "owner"}


def test_list_for_actor_returns_newest_first(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            for i in range(3):
                await audit.record(
                    s,
                    actor_sub="user-1",
                    action="voyage.create",
                    target_type="voyage",
                    target_id=f"v_{i}",
                    payload={"perspective": "owner"},
                )
            await s.commit()
        return await audit.list_for_actor(sessionmaker, "user-1")

    events = asyncio.run(go())
    assert [e.target_id for e in events] == ["v_2", "v_1", "v_0"]


def test_list_for_actor_isolates_actors(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            await audit.record(
                s,
                actor_sub="user-1",
                action="voyage.create",
                target_type="voyage",
                target_id="v_a",
            )
            await audit.record(
                s,
                actor_sub="user-2",
                action="voyage.create",
                target_type="voyage",
                target_id="v_b",
            )
            await s.commit()
        return (
            await audit.list_for_actor(sessionmaker, "user-1"),
            await audit.list_for_actor(sessionmaker, "user-2"),
        )

    user1, user2 = asyncio.run(go())
    assert [e.target_id for e in user1] == ["v_a"]
    assert [e.target_id for e in user2] == ["v_b"]


def test_list_for_actor_respects_limit(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            for i in range(10):
                await audit.record(
                    s,
                    actor_sub="user-1",
                    action="voyage.create",
                    target_type="voyage",
                    target_id=f"v_{i}",
                )
            await s.commit()
        return await audit.list_for_actor(sessionmaker, "user-1", limit=3)

    events = asyncio.run(go())
    assert len(events) == 3


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def test_redact_keeps_primitive_allowlist_values_as_is() -> None:
    payload = {
        "perspective": "owner",
        "from_stage": "done",
        "to_stage": "pending",
        "sandbox": True,
        "ses_message_id": "abc-123",
    }
    out = _redact(payload)
    assert out == payload


def test_redact_summarises_long_allowlisted_string() -> None:
    long = "x" * 200
    out = _redact({"voyage_id": long})
    assert out["voyage_id"] == f"<len:{len(long)}>"


def test_redact_drops_unknown_string_to_marker() -> None:
    out = _redact({"letter_markdown": "Dear Sirs, we write to claim demurrage..."})
    assert "letter_markdown" in out
    assert out["letter_markdown"].startswith("<len:")


def test_redact_drops_unknown_collection_to_marker() -> None:
    out = _redact({"flagged_events": [1, 2, 3]})
    assert out["flagged_events"] == "<list:3>"


def test_record_writes_redacted_payload(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            await audit.record(
                s,
                actor_sub="user-1",
                action="voyage.letter_email",
                target_type="voyage",
                target_id="v_abc",
                payload={
                    "recipients_to": ["claims@charterer.com"],
                    # Not allowlisted; >40 chars so it MUST collapse to <len:N>.
                    "letter_body": (
                        "Dear Sirs, we write to claim demurrage of EUR 84,375.00 "
                        "for the captioned voyage. Please remit within 30 days..."
                    ),
                    "sandbox": True,
                },
            )
            await s.commit()
        return await audit.list_for_actor(sessionmaker, "user-1")

    events = asyncio.run(go())
    assert events[0].payload["recipients_to"] == ["claims@charterer.com"]
    assert events[0].payload["sandbox"] is True
    assert events[0].payload["letter_body"].startswith("<len:")


def test_action_vocabulary_is_locked() -> None:
    """A new mutation route MUST add its action to the closed set in
    audit.py. The test reads the Literal at runtime so a typo is caught."""
    from typing import get_args

    args = set(get_args(audit.AuditAction))
    assert "voyage.create" in args
    assert "voyage.delete" in args
    assert "voyage.letter_email" in args
    assert "voyage.from_email" in args
    assert "voyage.status_change" in args
    assert "workspace.create" in args
    assert "workspace.invite" in args
    assert "workspace.accept" in args
