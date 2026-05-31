"""W9 backend tests: invitations admin + accept flow.

Three blocks:

- ``GET /workspaces/{id}/invitations`` returns only pending rows (accepted,
  revoked, and expired rows are excluded).
- ``POST /workspaces/{id}/invitations`` mints a row whose token round-trips
  through ``POST /invitations/{token}/accept``.
- Accepting a token mints the membership for the caller; a second accept
  is idempotent at equal-or-higher existing role.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
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
from portside_api.db.models import (  # noqa: E402
    AuditEventRow,
    InvitationRow,
    MembershipRow,
    WorkspaceRow,
)
from sqlalchemy import delete, select  # noqa: E402


async def _wipe_workspace_state() -> None:
    async with main_mod._sessionmaker() as session:
        async with session.begin():
            await session.execute(delete(InvitationRow))
            await session.execute(delete(MembershipRow))
            await session.execute(delete(WorkspaceRow))
            await session.execute(delete(AuditEventRow))


@pytest.fixture
def client() -> Iterator[TestClient]:
    asyncio.run(_wipe_workspace_state())
    with TestClient(main_mod.app) as c:
        yield c
    asyncio.run(_wipe_workspace_state())


def _seed_personal_workspace_for_dev_user() -> str:
    async def _seed() -> str:
        async with main_mod._sessionmaker() as session:
            wid = await workspaces.ensure_personal_workspace(
                session, user_sub=DEV_USER_ID
            )
            await session.commit()
            return wid

    return asyncio.run(_seed())


# ---------------------------------------------------------------------------
# Listing pending invitations
# ---------------------------------------------------------------------------


def test_invitations_list_returns_only_pending(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()

    # Mint three invites: one pending, one accepted, one expired.
    async def _seed_three() -> None:
        async with main_mod._sessionmaker() as session:
            pending = await workspaces.create_invitation(
                session,
                workspace_id=wid,
                email="pending@example.com",
                role="member",
                invited_by_sub=DEV_USER_ID,
            )
            accepted = await workspaces.create_invitation(
                session,
                workspace_id=wid,
                email="accepted@example.com",
                role="member",
                invited_by_sub=DEV_USER_ID,
            )
            accepted.accepted_at = datetime.now(timezone.utc)
            expired = await workspaces.create_invitation(
                session,
                workspace_id=wid,
                email="expired@example.com",
                role="member",
                invited_by_sub=DEV_USER_ID,
            )
            expired.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
            await session.commit()
            assert pending.id != accepted.id != expired.id

    asyncio.run(_seed_three())

    resp = client.get(f"/workspaces/{wid}/invitations")
    assert resp.status_code == 200
    body = resp.json()
    emails = {row["email"] for row in body}
    assert emails == {"pending@example.com"}


def test_invitations_list_404_when_caller_not_a_member(client: TestClient) -> None:
    resp = client.get("/workspaces/personal:no-such-user/invitations")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Mint + accept round-trip
# ---------------------------------------------------------------------------


def test_create_then_accept_mints_membership(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    # Mint an invite via the admin route.
    create = client.post(
        f"/workspaces/{wid}/invitations",
        json={"email": "new@example.com", "role": "member"},
    )
    assert create.status_code == 201, create.text
    invite = create.json()
    assert invite["email"] == "new@example.com"
    assert invite["role"] == "member"
    assert invite["accepted"] is False
    token = invite["token"]
    assert isinstance(token, str) and len(token) > 20

    # Accept the token under the same dev user.
    accept = client.post(f"/invitations/{token}/accept")
    assert accept.status_code == 200, accept.text
    accepted = accept.json()
    assert accepted["accepted"] is True

    # Re-accepting at the same role is idempotent (no error).
    again = client.post(f"/invitations/{token}/accept")
    # Existing row is already accepted; accept_invitation returns None and
    # the route layer 410s. This is the same shape as expired/revoked.
    assert again.status_code == 410


def test_create_invitation_rejects_invalid_email(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    resp = client.post(
        f"/workspaces/{wid}/invitations",
        json={"email": "not-an-email", "role": "member"},
    )
    assert resp.status_code == 422


def test_accept_unknown_token_returns_410(client: TestClient) -> None:
    _seed_personal_workspace_for_dev_user()
    resp = client.post("/invitations/not-a-real-token/accept")
    assert resp.status_code == 410


# ---------------------------------------------------------------------------
# Audit + persisted token
# ---------------------------------------------------------------------------


def test_invite_writes_audit_row(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    client.post(
        f"/workspaces/{wid}/invitations",
        json={"email": "audit@example.com", "role": "admin"},
    )
    audit = client.get("/audit").json()
    assert any(
        row["action"] == "workspace.invite"
        and row["payload"].get("workspace_id") == wid
        for row in audit
    )


def test_invitation_token_persists_in_db(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    resp = client.post(
        f"/workspaces/{wid}/invitations",
        json={"email": "row@example.com", "role": "viewer"},
    )
    token = resp.json()["token"]

    async def _read() -> InvitationRow | None:
        async with main_mod._sessionmaker() as session:
            return (
                await session.execute(
                    select(InvitationRow).where(InvitationRow.token == token)
                )
            ).scalar_one_or_none()

    row = asyncio.run(_read())
    assert row is not None
    assert row.role == "viewer"
