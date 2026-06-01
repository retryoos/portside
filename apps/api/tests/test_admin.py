"""Tests for admin observability: the gate, usage capture, and aggregates."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Iterator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from laytimely_api import admin, main as main_mod
from laytimely_api.auth import Principal
from laytimely_api.db.models import TokenUsageRow
from tests.conftest import run_wipe


@pytest.fixture
def client() -> Iterator[TestClient]:
    run_wipe()
    with TestClient(main_mod.app) as c:
        yield c
    run_wipe()


# --- cost estimate ----------------------------------------------------------


def test_cost_estimate_uses_per_model_pricing() -> None:
    # Sonnet: 1M in @ $3, 1M out @ $15.
    assert admin.est_cost("claude-sonnet-4-6", 1_000_000, 1_000_000) == 18.0
    # Opus is pricier.
    assert admin.est_cost("claude-opus-4-8", 1_000_000, 0) == 15.0
    # Unknown model falls back to Sonnet pricing.
    assert admin.est_cost("mystery", 1_000_000, 0) == 3.0


# --- gate -------------------------------------------------------------------


def test_require_admin_allows_allowlisted_email() -> None:
    p = asyncio.run(
        main_mod.require_admin(Principal(id="u", email="demo@laytimely.com"))
    )
    assert p.email == "demo@laytimely.com"


def test_require_admin_rejects_other_email() -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            main_mod.require_admin(Principal(id="u", email="nope@example.com"))
        )
    assert exc.value.status_code == 403


# --- aggregates over captured usage ----------------------------------------


def _seed_usage() -> None:
    async def _go() -> None:
        async with main_mod._sessionmaker() as session:
            session.add_all(
                [
                    TokenUsageRow(
                        at=datetime.now(timezone.utc),
                        actor_sub="u1",
                        voyage_id="v1",
                        feature="ExtractionResult",
                        model="claude-sonnet-4-6",
                        input_tokens=1000,
                        output_tokens=500,
                        cache_read_tokens=0,
                        cache_creation_tokens=0,
                        key_fp="abc123",
                        key_label="key-a",
                    ),
                    TokenUsageRow(
                        at=datetime.now(timezone.utc),
                        actor_sub="u1",
                        voyage_id="v1",
                        feature="DisputeAnalysis",
                        model="claude-opus-4-8",
                        input_tokens=2000,
                        output_tokens=1000,
                        cache_read_tokens=0,
                        cache_creation_tokens=0,
                        key_fp="abc123",
                        key_label="key-a",
                    ),
                ]
            )
            await session.commit()

    asyncio.run(_go())


def test_admin_overview_aggregates_usage(client: TestClient) -> None:
    _seed_usage()
    r = client.get("/admin/overview?days=30")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total_calls"] == 2
    assert d["total_input_tokens"] == 3000
    assert d["est_cost_usd"] > 0
    # One key label, two models, two features.
    assert [b["key"] for b in d["by_key"]] == ["key-a"]
    assert {b["key"] for b in d["by_model"]} == {
        "claude-opus-4-8",
        "claude-sonnet-4-6",
    }
    assert {b["key"] for b in d["by_feature"]} == {
        "ExtractionResult",
        "DisputeAnalysis",
    }


def test_admin_overview_counts_signups(client: TestClient) -> None:
    # A bootstrap signup writes an auth.signup audit row the dashboard counts.
    s = client.post(
        "/auth/signup",
        json={
            "email": "newbie@acme.com",
            "password": "password1",
            "bootstrap_code": "test-bootstrap",
        },
    )
    assert s.status_code == 200, s.text
    r = client.get("/admin/overview?days=1")
    assert r.status_code == 200
    assert r.json()["signups"] >= 1

    ev = client.get("/admin/events")
    assert ev.status_code == 200
    assert any(e["action"] == "auth.signup" for e in ev.json())
