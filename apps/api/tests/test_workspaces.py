"""Tests for the workspaces foundation (notes/architecture_weeks_5_to_8.md §2.1).

Five blocks:

- ``role_at_least`` honours the closed role lattice.
- ``ensure_personal_workspace`` is idempotent and mints owner membership.
- ``create_invitation`` writes a row with the expected role, expiry, token.
- ``accept_invitation`` mints membership, idempotent on re-accept, and
  refuses expired / revoked / already-accepted tokens.
- ``CreateInvitationRequest`` validates the email shape at the wire boundary
  without depending on `pydantic[email]`.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from laytimely_api import workspaces  # noqa: E402
from laytimely_api.db.engine import create_all, make_engine, make_sessionmaker  # noqa: E402
from laytimely_api.db.models import InvitationRow, MembershipRow, WorkspaceRow  # noqa: E402


@pytest.fixture
def sessionmaker(tmp_path: Path):
    url = f"sqlite+aiosqlite:///{tmp_path / 'workspaces.db'}"
    engine = make_engine(url)
    asyncio.run(create_all(engine))
    sm = make_sessionmaker(engine)
    yield sm
    asyncio.run(engine.dispose())


# ---------------------------------------------------------------------------
# Role lattice
# ---------------------------------------------------------------------------


def test_role_lattice_is_strict_ordering() -> None:
    assert workspaces.role_at_least("owner", "viewer")
    assert workspaces.role_at_least("admin", "member")
    assert workspaces.role_at_least("member", "viewer")
    assert workspaces.role_at_least("viewer", "viewer")
    assert not workspaces.role_at_least("viewer", "member")
    assert not workspaces.role_at_least("member", "admin")
    assert not workspaces.role_at_least("admin", "owner")


# ---------------------------------------------------------------------------
# ensure_personal_workspace
# ---------------------------------------------------------------------------


def test_ensure_personal_workspace_mints_owner_membership(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            wid, created = await workspaces.ensure_personal_workspace(
                s, user_sub="user-1", display_name="Dimitris"
            )
            assert created is True
            await s.commit()
            return wid

    wid = asyncio.run(go())
    assert wid == "personal:user-1"

    async def check():
        async with sessionmaker() as s:
            ws = await s.get(WorkspaceRow, wid)
            role = await workspaces.user_role_in_workspace(
                s, workspace_id=wid, user_sub="user-1"
            )
        return ws.name if ws else None, role

    name, role = asyncio.run(check())
    assert name == "Dimitris's workspace"
    assert role == "owner"


def test_ensure_personal_workspace_is_idempotent(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            wid1, created1 = await workspaces.ensure_personal_workspace(
                s, user_sub="u"
            )
            wid2, created2 = await workspaces.ensure_personal_workspace(
                s, user_sub="u"
            )
            assert created1 is True
            assert created2 is False
            await s.commit()
        async with sessionmaker() as s:
            count = (
                await s.execute(
                    workspaces.select(WorkspaceRow).where(WorkspaceRow.id == wid1)
                )
            ).scalars().all()
            memberships = (
                await s.execute(
                    workspaces.select(MembershipRow).where(
                        MembershipRow.workspace_id == wid1
                    )
                )
            ).scalars().all()
        return wid1, wid2, len(count), len(memberships)

    wid1, wid2, ws_count, mem_count = asyncio.run(go())
    assert wid1 == wid2
    assert ws_count == 1
    assert mem_count == 1


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


def test_create_invitation_writes_a_token_and_14_day_ttl(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            await workspaces.ensure_personal_workspace(s, user_sub="admin-1")
            row = await workspaces.create_invitation(
                s,
                workspace_id="personal:admin-1",
                email="Mate@partner.com",
                role="member",
                invited_by_sub="admin-1",
            )
            await s.commit()
            return row

    row = asyncio.run(go())
    assert row.email == "mate@partner.com"  # lowercased
    assert row.role == "member"
    assert len(row.token) >= 32
    delta = row.expires_at - row.invited_at
    assert timedelta(days=13, hours=23) <= delta <= timedelta(days=14, minutes=1)


def test_accept_invitation_mints_membership(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            await workspaces.ensure_personal_workspace(s, user_sub="admin-1")
            inv = await workspaces.create_invitation(
                s,
                workspace_id="personal:admin-1",
                email="mate@partner.com",
                role="member",
                invited_by_sub="admin-1",
            )
            await s.commit()
            token = inv.token
        async with sessionmaker() as s:
            accepted = await workspaces.accept_invitation(
                s, token=token, acceptor_sub="user-mate"
            )
            await s.commit()
        async with sessionmaker() as s:
            role = await workspaces.user_role_in_workspace(
                s, workspace_id="personal:admin-1", user_sub="user-mate"
            )
        return accepted is not None, role

    ok, role = asyncio.run(go())
    assert ok
    assert role == "member"


def test_accept_invitation_rejects_expired_token(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            await workspaces.ensure_personal_workspace(s, user_sub="admin-1")
            inv = await workspaces.create_invitation(
                s,
                workspace_id="personal:admin-1",
                email="mate@partner.com",
                role="member",
                invited_by_sub="admin-1",
            )
            # Backdate the expiry so it falls outside the 14-day window.
            inv.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
            await s.commit()
            token = inv.token
        async with sessionmaker() as s:
            accepted = await workspaces.accept_invitation(
                s, token=token, acceptor_sub="user-mate"
            )
            await s.commit()
        return accepted

    assert asyncio.run(go()) is None


def test_accept_invitation_rejects_unknown_token(sessionmaker) -> None:
    async def go():
        async with sessionmaker() as s:
            return await workspaces.accept_invitation(
                s, token="not-a-real-token", acceptor_sub="anyone"
            )

    assert asyncio.run(go()) is None


def test_accept_invitation_idempotent_on_existing_higher_role(sessionmaker) -> None:
    """If the acceptor is already a member at a role >= the invite, no new
    membership row should be written."""

    async def go():
        async with sessionmaker() as s:
            await workspaces.ensure_personal_workspace(s, user_sub="admin-1")
            # admin-1 is already owner of their workspace. Invite them as a
            # plain member; accept should not downgrade them.
            inv = await workspaces.create_invitation(
                s,
                workspace_id="personal:admin-1",
                email="self@x.com",
                role="member",
                invited_by_sub="admin-1",
            )
            await s.commit()
            token = inv.token
        async with sessionmaker() as s:
            accepted = await workspaces.accept_invitation(
                s, token=token, acceptor_sub="admin-1"
            )
            await s.commit()
        async with sessionmaker() as s:
            memberships = (
                await s.execute(
                    workspaces.select(MembershipRow).where(
                        MembershipRow.workspace_id == "personal:admin-1",
                        MembershipRow.user_sub == "admin-1",
                    )
                )
            ).scalars().all()
        return accepted is not None, [m.role for m in memberships]

    ok, roles = asyncio.run(go())
    assert ok
    assert roles == ["owner"]


# ---------------------------------------------------------------------------
# Wire model validation
# ---------------------------------------------------------------------------


def test_create_invitation_request_validates_email() -> None:
    with pytest.raises(Exception):
        workspaces.CreateInvitationRequest(email="not-an-email", role="member")


def test_create_invitation_request_defaults_role_to_member() -> None:
    req = workspaces.CreateInvitationRequest(email="a@b.com")
    assert req.role == "member"
