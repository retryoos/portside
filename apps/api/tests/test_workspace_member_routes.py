"""W8 backend tests: workspace listing for the caller + member removal.

Three blocks:

- ``GET /me/workspaces`` always yields at least the caller's personal
  workspace (ensure_personal_workspace is invoked on read).
- ``DELETE /workspaces/{id}/members/{sub}`` drops the row, audits it, and
  serves 204; 404 when the membership does not exist.
- The last-owner guard refuses with 409; once another owner exists, the
  original owner can be removed cleanly.
"""

from __future__ import annotations

import asyncio
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
from portside_api.db.models import (  # noqa: E402
    AuditEventRow,
    InvitationRow,
    MembershipRow,
    WorkspaceRow,
)
from sqlalchemy import delete  # noqa: E402


async def _wipe_workspace_state() -> None:
    """Drop every workspace-related row so tests do not bleed into each other.

    The shared SQLite file under ``portside.db`` is reused across the test
    session because ``_sessionmaker`` is module-level; isolation is by
    table truncation.
    """
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


def _seed_second_owner(workspace_id: str, other_sub: str) -> None:
    async def _seed() -> None:
        async with main_mod._sessionmaker() as session:
            session.add(
                MembershipRow(
                    workspace_id=workspace_id,
                    user_sub=other_sub,
                    role="owner",
                )
            )
            await session.commit()

    asyncio.run(_seed())


def _seed_admin_membership(workspace_id: str, other_sub: str) -> None:
    async def _seed() -> None:
        async with main_mod._sessionmaker() as session:
            session.add(
                MembershipRow(
                    workspace_id=workspace_id,
                    user_sub=other_sub,
                    role="admin",
                )
            )
            await session.commit()

    asyncio.run(_seed())


# ---------------------------------------------------------------------------
# GET /me/workspaces
# ---------------------------------------------------------------------------


def test_me_workspaces_creates_personal_workspace_if_missing(
    client: TestClient,
) -> None:
    resp = client.get("/me/workspaces")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert any(row["workspace"]["id"] == f"personal:{DEV_USER_ID}" for row in body)
    # The caller is the owner of their personal workspace.
    personal = [
        row for row in body if row["workspace"]["id"] == f"personal:{DEV_USER_ID}"
    ][0]
    assert personal["role"] == "owner"


def test_me_workspaces_is_idempotent(client: TestClient) -> None:
    first = client.get("/me/workspaces").json()
    second = client.get("/me/workspaces").json()
    assert len(first) == len(second)


# ---------------------------------------------------------------------------
# DELETE /workspaces/{id}/members/{sub}
# ---------------------------------------------------------------------------


def test_member_remove_returns_204_and_records_audit(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    other_sub = "user-to-evict"
    _seed_admin_membership(wid, other_sub)

    resp = client.delete(f"/workspaces/{wid}/members/{other_sub}")
    assert resp.status_code == 204, resp.text

    # Audit row was written under the calling actor.
    audit = client.get("/audit").json()
    assert any(
        row["action"] == "workspace.member_remove"
        and row["target_id"] == f"{wid}:{other_sub}"
        for row in audit
    )


def test_member_remove_404_when_membership_missing(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    resp = client.delete(f"/workspaces/{wid}/members/no-such-user")
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"]["code"] == "not_found"


def test_member_remove_refuses_last_owner(client: TestClient) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    # Dev user is the only owner of the personal workspace.
    resp = client.delete(f"/workspaces/{wid}/members/{DEV_USER_ID}")
    assert resp.status_code == 409
    body = resp.json()
    assert body["detail"]["code"] == "last_owner"


def test_member_remove_allows_owner_when_another_owner_exists(
    client: TestClient,
) -> None:
    wid = _seed_personal_workspace_for_dev_user()
    co_owner = "second-owner"
    _seed_second_owner(wid, co_owner)
    # Now the dev user can be removed.
    resp = client.delete(f"/workspaces/{wid}/members/{DEV_USER_ID}")
    assert resp.status_code == 204, resp.text
    # The co-owner remains.

    async def _check() -> bool:
        async with main_mod._sessionmaker() as session:
            role = await workspaces.user_role_in_workspace(
                session, workspace_id=wid, user_sub=co_owner
            )
        return role == "owner"

    assert asyncio.run(_check())
