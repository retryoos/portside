"""Multi-tenant workspaces (notes/architecture_weeks_5_to_8.md §2.1).

Foundation only: schema, role helper, invitation token mint + accept, and the
``require_workspace_role(min_role)`` FastAPI dependency. The route layer
landing UI on the frontend ships as a follow-up (Roman's lane); this module
ships the backend contract so the UI can build against it.

Roles (closed)
--------------

``owner``   - one per workspace at minimum; cannot be removed while last;
              can do everything including billing.
``admin``   - manage members, invitations, and settings; cannot remove the
              last owner.
``member``  - day-to-day use; create and manage voyages.

The ordering is a strict lattice: every higher role can do everything a lower
role can. ``require_workspace_role(min_role)`` enforces by integer index.

Feature flag
------------

``settings.workspaces_ui`` is False by default. When off, the route layer
still mints a personal workspace for each user on first auth (so the data
contract is consistent), but the dashboards never surface the workspace
switcher and every voyage routes through the caller's personal workspace.
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .auth import Principal, get_current_user
from .db.models import InvitationRow, MembershipRow, WorkspaceRow

Role = Literal["owner", "admin", "member"]
_ROLE_ORDER: tuple[Role, ...] = ("member", "admin", "owner")
_ROLE_LEVEL: dict[Role, int] = {role: i for i, role in enumerate(_ROLE_ORDER)}

# 14-day invitation TTL. After this, the accept route 410s.
_INVITATION_TTL = timedelta(days=14)


# ---------------------------------------------------------------------------
# Wire models
# ---------------------------------------------------------------------------


class Workspace(BaseModel):
    id: str
    name: str
    plan: str


class Member(BaseModel):
    user_sub: str
    role: Role
    # Populated by the members route via a join on the users table so the
    # admin UI shows a human (email/name) instead of an opaque id. Both stay
    # optional: a membership can in principle reference a user row that has no
    # email (legacy/seed), and the UI falls back to a shortened id.
    email: str | None = None
    name: str | None = None


class Invitation(BaseModel):
    id: int
    workspace_id: str
    email: str
    role: Role
    token: str
    invited_by_sub: str
    invited_at: str  # ISO-8601
    expires_at: str
    accepted: bool
    revoked: bool


class CreateInvitationRequest(BaseModel):
    email: str
    role: Role = Field(default="member")

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        if not _EMAIL_RE.match(value):
            raise ValueError(f"invalid email address: {value!r}")
        return value


# ---------------------------------------------------------------------------
# Helpers (pure / async)
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def role_at_least(role: Role, min_role: Role) -> bool:
    """True if ``role`` is the same or higher than ``min_role``."""
    return _ROLE_LEVEL[role] >= _ROLE_LEVEL[min_role]


# RFC 5322 dot-atom: A-Z a-z 0-9 and a small set of specials. We restrict
# further to the safe subset that survives every mail client we care about
# (no specials beyond ``_-.``); colons go to ``-`` (a workspace_id
# ``personal:<sub>`` becomes ``personal-<sub>``).
_INBOX_SAFE_RE = re.compile(r"[^A-Za-z0-9_.-]")


def inbox_local_part(workspace_id: str) -> str:
    """RFC 5322-safe local part derived from the workspace id (W7, hardened
    post-review #17).

    Steps: lowercase, swap ``:`` for ``-``, drop any remaining char outside
    the safe class, collapse consecutive ``-``. The result is always a
    valid dot-atom local part regardless of what the workspace_id looks
    like — important once non-personal workspace_ids land and may not
    be UUID-shaped.
    """
    swapped = workspace_id.strip().lower().replace(":", "-").replace(" ", "-")
    cleaned = _INBOX_SAFE_RE.sub("-", swapped)
    # Collapse runs of ``-`` and trim leading/trailing separators so the
    # address is also visually clean.
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    cleaned = cleaned.strip("-.")
    if not cleaned:
        # Pathological input (e.g. all separators). Fall back to a safe
        # sentinel + the truncated original hash for traceability.
        cleaned = f"ws-{abs(hash(workspace_id)) % (10**10):010d}"
    return cleaned


def inbox_address(workspace_id: str, domain: str) -> str:
    """The forward-to address surfaced by the /settings/inbox page (W7)."""
    return f"{inbox_local_part(workspace_id)}@{domain}"


async def ensure_personal_workspace(
    session: AsyncSession,
    *,
    user_sub: str,
    display_name: Optional[str] = None,
) -> tuple[str, bool]:
    """Create the caller's personal workspace if one does not exist.

    Returns ``(workspace_id, created)``. ``created`` is True only when this
    call inserted a new row, so the caller can skip the commit on the hot
    no-op path. The personal workspace id is a deterministic
    ``personal:<sub>`` string so later code (audit log, email-in address)
    does not need an extra lookup to derive it. Idempotent: re-running on a
    user that already has the row is a no-op (no commit needed).
    """
    workspace_id = f"personal:{user_sub}"
    existing = await session.get(WorkspaceRow, workspace_id)
    if existing is not None:
        return workspace_id, False
    name = f"{display_name or user_sub}'s workspace"
    session.add(WorkspaceRow(id=workspace_id, name=name, plan="self_serve"))
    # Flush before the FK dependent insert so SQLite's deferred FK check
    # passes; SQLAlchemy does not topologically sort independent rows.
    await session.flush()
    session.add(
        MembershipRow(
            workspace_id=workspace_id,
            user_sub=user_sub,
            role="owner",
        )
    )
    await session.flush()
    return workspace_id, True


async def user_role_in_workspace(
    session: AsyncSession,
    *,
    workspace_id: str,
    user_sub: str,
) -> Optional[Role]:
    row = (
        await session.execute(
            select(MembershipRow).where(
                MembershipRow.workspace_id == workspace_id,
                MembershipRow.user_sub == user_sub,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    return row.role  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


def _mint_token() -> str:
    """URL-safe 32-byte secret. ``secrets.token_urlsafe(32)`` yields ~43 chars
    of entropy, plenty for a 14-day invitation."""
    return secrets.token_urlsafe(32)


async def create_invitation(
    session: AsyncSession,
    *,
    workspace_id: str,
    email: str,
    role: Role,
    invited_by_sub: str,
) -> InvitationRow:
    """Persist a new invitation row. Does NOT send the email; the route
    layer enqueues an SES job (or, in dev, prints the link to the log)."""
    row = InvitationRow(
        workspace_id=workspace_id,
        email=email.strip().lower(),
        role=role,
        token=_mint_token(),
        invited_by_sub=invited_by_sub,
        expires_at=_now_utc() + _INVITATION_TTL,
    )
    session.add(row)
    await session.flush()
    return row


async def accept_invitation(
    session: AsyncSession,
    *,
    token: str,
    acceptor_sub: str,
) -> Optional[InvitationRow]:
    """Resolve a token to its invitation; mint the matching membership if the
    invite is current.

    Returns the accepted row, or ``None`` on bad token / expired / revoked /
    already accepted by a *different* user. The route handler is responsible
    for the HTTP status mapping.

    Idempotency rule (W9 fix): if this token was already accepted AND the
    caller already holds membership at the invited role or higher, treat
    the second accept as a success (return the original row). This is the
    "hit back, see the success page again" path; refusing here forces the
    user through a confusing 410 after a perfectly normal accept.
    """
    inv = (
        await session.execute(
            select(InvitationRow).where(InvitationRow.token == token)
        )
    ).scalar_one_or_none()
    if inv is None:
        return None
    if inv.revoked_at is not None:
        return None
    existing_role = await user_role_in_workspace(
        session, workspace_id=inv.workspace_id, user_sub=acceptor_sub
    )
    if inv.accepted_at is not None:
        # Already used. Accept idempotently if and only if the *same* caller
        # consumed it last time (tracked via accepted_by_sub). A different
        # user touching the same used token gets 410, regardless of their
        # existing role in the workspace.
        if inv.accepted_by_sub == acceptor_sub:
            return inv
        return None
    expires_at = inv.expires_at
    if expires_at.tzinfo is None:
        # SQLite returns naive UTC; treat as such.
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < _now_utc():
        return None
    # First-time accept: mint membership unless the caller is already at
    # this role or higher (e.g. an owner accepting their own admin invite).
    if existing_role is None or not role_at_least(existing_role, inv.role):  # type: ignore[arg-type]
        session.add(
            MembershipRow(
                workspace_id=inv.workspace_id,
                user_sub=acceptor_sub,
                role=inv.role,
            )
        )
    inv.accepted_at = _now_utc()
    inv.accepted_by_sub = acceptor_sub
    await session.flush()
    return inv


async def get_pending_invitation(
    session: AsyncSession,
    *,
    token: str,
) -> Optional[InvitationRow]:
    """Return the invitation for ``token`` iff it is still usable (not
    accepted, not revoked, not expired). Used by the invite-only signup gate to
    validate a token before creating an account. Does not consume the invite;
    acceptance happens separately."""
    inv = (
        await session.execute(
            select(InvitationRow).where(InvitationRow.token == token)
        )
    ).scalar_one_or_none()
    if inv is None or inv.accepted_at is not None or inv.revoked_at is not None:
        return None
    expires_at = inv.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < _now_utc():
        return None
    return inv


async def list_pending_invitations(
    session: AsyncSession,
    *,
    workspace_id: str,
) -> list[InvitationRow]:
    """Workspace admin view: every invitation that is not yet accepted,
    revoked, or expired. Newest first.

    Filters server-side (post-review #7). Postgres compares ``expires_at``
    against the timezone-aware ``now()`` cleanly; SQLite (dev) stores the
    column as ISO-8601 naive UTC which compares lexicographically against
    a naive ``datetime.utcnow()``. We feed the comparison a UTC-naive value
    so the SQL works on both backends without backend detection.
    """
    # tzinfo-stripped UTC: compares cleanly against SQLite's naive storage
    # and against Postgres's timezone-aware column when both sides drop
    # zone info for the comparison.
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = (
        await session.execute(
            select(InvitationRow)
            .where(
                InvitationRow.workspace_id == workspace_id,
                InvitationRow.accepted_at.is_(None),
                InvitationRow.revoked_at.is_(None),
                InvitationRow.expires_at > now_naive,
            )
            .order_by(InvitationRow.invited_at.desc())
        )
    ).scalars().all()
    return list(rows)


# ---------------------------------------------------------------------------
# Membership management (W8)
# ---------------------------------------------------------------------------


class MemberRemoveError(RuntimeError):
    """Carries a stable code so the route handler maps to a precise HTTP
    status without inspecting strings. The two error modes the route layer
    needs to distinguish are "no such member" (404) and "would leave the
    workspace with no owner" (409)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


async def list_memberships_for_user(
    session: AsyncSession,
    *,
    user_sub: str,
) -> list[tuple[WorkspaceRow, Role]]:
    """Every workspace the user is a member of, with their role in each.

    Used by ``GET /me/workspaces`` to populate the workspace switcher and
    the W8 /settings/members page. Ordered by workspace name so the
    dropdown is stable across reloads.
    """
    rows = (
        await session.execute(
            select(MembershipRow, WorkspaceRow)
            .join(WorkspaceRow, WorkspaceRow.id == MembershipRow.workspace_id)
            .where(MembershipRow.user_sub == user_sub)
            .order_by(WorkspaceRow.name)
        )
    ).all()
    return [(ws, mem.role) for (mem, ws) in rows]  # type: ignore[return-value]


async def change_member_role(
    session: AsyncSession,
    *,
    workspace_id: str,
    user_sub: str,
    new_role: Role,
) -> MembershipRow:
    """Promote or demote a member (review #11).

    Refusals raise ``MemberRemoveError`` with a stable code (re-using the
    type so the route handler has one error path for both endpoints):

    - ``not_found``: the user has no membership in this workspace.
    - ``last_owner``: demoting the only owner is refused for the same
      reason removing the only owner is refused — the workspace must
      always keep at least one owner. Promote another member first.

    No-ops (target already at ``new_role``) succeed silently.
    """
    row = (
        await session.execute(
            select(MembershipRow).where(
                MembershipRow.workspace_id == workspace_id,
                MembershipRow.user_sub == user_sub,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise MemberRemoveError(
            "not_found", f"no membership for {user_sub} in {workspace_id}"
        )
    if row.role == new_role:
        return row
    if row.role == "owner" and new_role != "owner":
        other_owner = (
            await session.execute(
                select(MembershipRow.user_sub)
                .where(
                    MembershipRow.workspace_id == workspace_id,
                    MembershipRow.role == "owner",
                    MembershipRow.user_sub != user_sub,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if other_owner is None:
            raise MemberRemoveError(
                "last_owner",
                "cannot demote the only owner; promote another member to owner first",
            )
    row.role = new_role
    await session.flush()
    return row


async def revoke_invitation(
    session: AsyncSession,
    *,
    invitation_id: int,
    workspace_id: str,
) -> Optional[InvitationRow]:
    """Mark a pending invitation as revoked (review #10).

    Returns the updated row on success, or ``None`` if the invitation does
    not belong to the workspace, has already been accepted, or has already
    been revoked. The route handler maps None to 410.
    """
    row = await session.get(InvitationRow, invitation_id)
    if row is None or row.workspace_id != workspace_id:
        return None
    if row.accepted_at is not None or row.revoked_at is not None:
        return None
    row.revoked_at = _now_utc()
    await session.flush()
    return row


async def remove_member(
    session: AsyncSession,
    *,
    workspace_id: str,
    user_sub: str,
) -> MembershipRow:
    """Drop a single membership row.

    Two refusal modes (both raise ``MemberRemoveError`` with a stable code):

    - ``not_found``: the user has no membership in this workspace.
    - ``last_owner``: the target is the only owner. Workspaces must always
      have at least one owner so a stranded workspace cannot be created by
      removing the last billing-responsible member. The admin must promote
      another member first.

    On success the returned row is the just-deleted one (with its prior
    role field intact) so the route layer can audit it.
    """
    row = (
        await session.execute(
            select(MembershipRow).where(
                MembershipRow.workspace_id == workspace_id,
                MembershipRow.user_sub == user_sub,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise MemberRemoveError(
            "not_found", f"no membership for {user_sub} in {workspace_id}"
        )
    if row.role == "owner":
        # Refuse if this is the only owner. Querying for any other owner row
        # is cheaper than counting all owners.
        other_owner = (
            await session.execute(
                select(MembershipRow.user_sub)
                .where(
                    MembershipRow.workspace_id == workspace_id,
                    MembershipRow.role == "owner",
                    MembershipRow.user_sub != user_sub,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if other_owner is None:
            raise MemberRemoveError(
                "last_owner",
                "cannot remove the only owner; promote another member to owner first",
            )
    captured = MembershipRow(
        workspace_id=row.workspace_id,
        user_sub=row.user_sub,
        role=row.role,
    )
    await session.delete(row)
    await session.flush()
    return captured


def to_invitation(row: InvitationRow) -> Invitation:
    return Invitation(
        id=row.id,
        workspace_id=row.workspace_id,
        email=row.email,
        role=row.role,  # type: ignore[arg-type]
        token=row.token,
        invited_by_sub=row.invited_by_sub,
        invited_at=row.invited_at.isoformat(),
        expires_at=row.expires_at.isoformat(),
        accepted=row.accepted_at is not None,
        revoked=row.revoked_at is not None,
    )


# ---------------------------------------------------------------------------
# FastAPI dependency: require_workspace_role(min_role)
# ---------------------------------------------------------------------------


def require_workspace_role(
    min_role: Role,
    sessionmaker: async_sessionmaker[AsyncSession],
):
    """Build a FastAPI dependency that resolves the caller's role in the
    target workspace (URL path parameter ``workspace_id``) and 403s if their
    role is below ``min_role``.

    Usage:

        deps_member = require_workspace_role("member", _sessionmaker)

        @app.get("/workspaces/{workspace_id}/voyages")
        async def list_workspace_voyages(
            workspace_id: str,
            principal: Annotated[Principal, Depends(deps_member)],
        ): ...

    The dependency returns the ``Principal`` so the route gets the user
    object without redeclaring ``Depends(get_current_user)``.
    """

    async def _resolve(
        workspace_id: str,
        principal: Annotated[Principal, Depends(get_current_user)],
    ) -> Principal:
        async with sessionmaker() as session:
            role = await user_role_in_workspace(
                session, workspace_id=workspace_id, user_sub=principal.id
            )
        if role is None:
            raise HTTPException(status_code=404, detail="workspace not found")
        if not role_at_least(role, min_role):  # type: ignore[arg-type]
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "workspace_role_required",
                    "required": min_role,
                    "actual": role,
                },
            )
        return principal

    return _resolve
