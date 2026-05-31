"""Tests for the inbox-address helpers + route (W7).

The deterministic address derivation lives in ``portside_api/workspaces.py``;
these tests pin both the helper and the route surface so the W7 frontend can
rely on it.
"""

from __future__ import annotations

import asyncio
import dataclasses
import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from portside_api import main as main_mod, workspaces  # noqa: E402
from portside_api.auth import DEV_USER_ID  # noqa: E402
from tests.conftest import run_wipe  # noqa: E402


# ---------------------------------------------------------------------------
# Helper: address shape
# ---------------------------------------------------------------------------


def test_inbox_local_part_replaces_colon() -> None:
    assert workspaces.inbox_local_part("personal:abc123") == "personal-abc123"


def test_inbox_local_part_passes_through_clean_id() -> None:
    assert workspaces.inbox_local_part("ws_acme") == "ws_acme"


def test_inbox_local_part_strips_unsafe_chars() -> None:
    """Review #17: workspace_id with spaces / specials produces a safe
    local part rather than an invalid email address."""
    assert workspaces.inbox_local_part("ws bad slug") == "ws-bad-slug"
    assert workspaces.inbox_local_part("ws_acme!") == "ws_acme"
    assert workspaces.inbox_local_part("UPPER:CASE") == "upper-case"


def test_inbox_local_part_pathological_falls_back_to_sentinel() -> None:
    """A workspace_id made entirely of separators must still produce a
    deliverable address."""
    out = workspaces.inbox_local_part("---")
    assert out.startswith("ws-")
    assert "@" not in out


def test_inbox_address_combines_local_part_and_domain() -> None:
    assert (
        workspaces.inbox_address("personal:abc", "in.laytimely.com")
        == "personal-abc@in.laytimely.com"
    )


# ---------------------------------------------------------------------------
# Route: GET /workspaces/{id}/inbox-address
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The route uses the real _sessionmaker so it can hit the admin gate.
    # Wipe workspace state on entry + exit so we don't inherit memberships
    # from sibling test files (they share the SQLite file).
    run_wipe()
    with TestClient(main_mod.app) as c:
        yield c
    run_wipe()


def _seed_personal_workspace_for_dev_user() -> str:
    async def _seed() -> str:
        async with main_mod._sessionmaker() as session:
            wid, _ = await workspaces.ensure_personal_workspace(
                session, user_sub=DEV_USER_ID
            )
            await session.commit()
            return wid

    return asyncio.run(_seed())


def test_inbox_address_route_returns_workspace_address(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        main_mod,
        "settings",
        dataclasses.replace(main_mod.settings, inbox_domain="in.laytimely.com"),
    )
    wid = _seed_personal_workspace_for_dev_user()
    resp = client.get(f"/workspaces/{wid}/inbox-address")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["format"] == "forward_to"
    expected_local = wid.replace(":", "-")
    assert body["address"] == f"{expected_local}@in.laytimely.com"


def test_inbox_address_route_honours_inbox_domain_setting(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        main_mod,
        "settings",
        dataclasses.replace(main_mod.settings, inbox_domain="in.dev.example"),
    )
    wid = _seed_personal_workspace_for_dev_user()
    resp = client.get(f"/workspaces/{wid}/inbox-address")
    assert resp.status_code == 200
    assert resp.json()["address"].endswith("@in.dev.example")


def test_inbox_address_route_404_when_caller_not_a_member(
    client: TestClient,
) -> None:
    resp = client.get("/workspaces/personal:no-such-user/inbox-address")
    # The admin gate resolves the caller's role first; missing membership
    # surfaces as a 404 ("workspace not found" from require_workspace_role).
    assert resp.status_code == 404
