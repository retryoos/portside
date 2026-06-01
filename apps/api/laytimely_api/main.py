"""FastAPI app + routes for the Laytimely backend.

Endpoints:
    POST /voyages                 upload CP/NOR/SoF PDFs, kick off the pipeline in
                                  the background, return the voyage_id immediately
                                  so the frontend can poll for staged progress
                                  (notes/02-architecture.md §2).
    GET  /voyages/{id}            fetch the current VoyageState (polled ~500ms).
    POST /voyages/{id}/revise     inline-revise a letter/narrative segment
                                  (notes/13-inline-revision.md).
    DELETE /voyages/{id}          delete a voyage (owner-scoped).
    GET  /me                      the current authenticated principal.
    GET  /healthz                 liveness probe.

State is persisted relationally (see db/); requests are scoped to the
authenticated user (Cognito JWT, or a dev user when DEV_AUTH is on).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    Form,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import (
    accounts,
    admin as admin_mod,
    audit,
    defense,
    pipeline,
    researcher,
    reviser,
    usage as token_usage,
    workspaces,
)
from .audit import AuditEvent
from .auth import DEV_USER_EMAIL, DEV_USER_ID, Principal, get_current_user
from .defense import RebuttalPacket
from .analyst_citations import FlaggedEventCitations
from .agents import analyst
from .claim_strength import (
    FlaggedEventStrength,
    build_panels as build_strength_panels,
    derive_model_panel_from_event,
)
from .evidence_checklist import (
    EvidenceChecklist,
    build_checklist as build_evidence_checklist,
)
from .inbox_address import InboxAddressResponse
from .researcher import EvidenceBundle
from .email import (
    EmailErrorCode,
    EmailSendError,
    LetterEmailRequest,
    SesSendResult,
    send_claim_letter,
)
from .email import invitations as invitation_email
from .db.models import WorkspaceRow as _WorkspaceRow
from .exports import excel as excel_export
from .inbox import (
    INBOUND_HMAC_HEADER,
    InboundError,
    InboundErrorCode,
    match_voyage,
    parse_message,
    verify_signature,
)
from .researcher import EvidenceItem
from .db.engine import make_engine, make_sessionmaker, run_migrations
from .fixtures import seed_voyages
from .limits import SlidingWindowRateLimiter, client_key, validate_and_read
from .pipeline import GENERIC_PIPELINE_ERROR
from .objects import (
    StoredDocument,
    VoyageDocumentInfo,
    build_key,
    make_object_store,
)
from .reviser import ApplyRevisionRequest, ReviseRequest, ReviseResponse
from .schemas import (
    Perspective,
    StatusUpdate,
    VesselSummary,
    VoyageState,
    VoyageSummary,
)
from .settings import settings
from .storage import SqlVoyageStore, VoyageStore

logger = logging.getLogger("laytimely_api")

# Relational store, shared for the process lifetime. The engine is lazy
# (no connection until first use), so constructing it at import is side-effect
# free; tests monkeypatch ``store`` with an InMemoryStore before startup.
_engine = make_engine(settings.database_url)
_sessionmaker = make_sessionmaker(_engine)
store: VoyageStore = SqlVoyageStore(_sessionmaker)
# Let the token-usage capture persist via the same sessionmaker (it cannot
# import main without a cycle, so we hand it the maker here).
token_usage.bind_sessionmaker(_sessionmaker)


async def _audit(
    actor_sub: str | None,
    action: audit.AuditAction,
    target_type: audit.AuditTarget,
    target_id: str,
    payload: dict | None = None,
) -> None:
    """Write one audit row in a fresh, short-lived session.

    Best-effort: failures are logged but never propagate to the caller. The
    audit trail is the second-best source of truth; we never block a real
    mutation on it.
    """
    try:
        async with _sessionmaker() as session:
            await audit.record(
                session,
                actor_sub=actor_sub,
                action=action,
                target_type=target_type,
                target_id=target_id,
                payload=payload,
            )
            await session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("audit.record failed for %s/%s", action, target_id)

# Object storage for uploaded PDFs (S3 in prod, local dir otherwise). Tests
# monkeypatch this with a LocalObjectStore pointed at a temp dir.
object_store = make_object_store()

# Hold strong references to in-flight background tasks. asyncio.create_task only
# weakly references its task, so without this the pipeline task can be GC'd /
# cancelled mid-run.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """On startup: migrate the schema (SQL backend only) and seed the demo cases
    if the store is empty. Seeding only-when-empty means a restart preserves real
    voyages instead of clobbering them (the point of persistence). Alembic spins
    up its own event loop, so run it off-thread to avoid nesting loops."""
    if isinstance(store, SqlVoyageStore):
        await asyncio.to_thread(run_migrations, settings.database_url)
        # Recover runs interrupted by a prior instance/deploy (stuck in a
        # non-terminal stage) so the UI doesn't poll them forever.
        reaped = await store.reap_stale_processing(settings.stale_run_seconds)
        if reaped:
            logger.info("reaped %d interrupted voyage run(s) on startup", reaped)
        # Audit retention reaper (review #9): drop rows older than the
        # configured horizon so the audit table stays bounded.
        retained = await audit.reap_older_than(
            _sessionmaker, retention_days=settings.audit_retention_days
        )
        if retained:
            logger.info(
                "reaped %d audit row(s) older than %dd",
                retained, settings.audit_retention_days,
            )
        # The seeded demo voyages are owned by the dev user so they remain
        # visible under owner-scoping in dev (DEV_AUTH) mode.
        await store.ensure_user(DEV_USER_ID, DEV_USER_EMAIL)
    if not await store.list():
        for state in seed_voyages():
            await store.save(state, owner_user_id=DEV_USER_ID)
    yield
    await _engine.dispose()


app = FastAPI(
    title="Laytimely API",
    version="0.1.0",
    lifespan=lifespan,
    # Interactive docs + schema are off unless EXPOSE_DOCS=1 so a production
    # deploy does not hand out a clickable map of its (currently open) surface.
    docs_url="/docs" if settings.expose_docs else None,
    redoc_url="/redoc" if settings.expose_docs else None,
    openapi_url="/openapi.json" if settings.expose_docs else None,
)

# CORS allowlist comes from settings.cors_origins (notes/02-architecture.md §12):
# local dev defaults to http://localhost:3000; add the Amplify domain on deploy
# via the CORS_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Baseline security headers on every response. The API serves JSON and file
# downloads (never HTML it renders itself), so a locked-down CSP is safe:
# `default-src 'none'` plus `frame-ancestors 'none'` blocks framing/clickjacking
# and any subresource loads. HSTS is ignored by browsers over plain HTTP (local
# dev) and enforced once the service is fronted by HTTPS (App Runner).
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):  # noqa: ANN001
    response = await call_next(request)
    for header, value in _SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response


# Coarse per-caller rate limit for the paid pipeline trigger (POST /voyages):
# unauthenticated demo mode + an Anthropic-backed pipeline means an unbounded
# endpoint is a cost/DoS amplifier. Tune via RATE_LIMIT_* env vars; 0 disables.
voyage_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


async def enforce_voyage_rate_limit(request: Request) -> None:
    """Reject (429) once a caller exceeds the POST /voyages budget."""
    if not voyage_rate_limiter.allow(client_key(request)):
        raise HTTPException(
            status_code=429,
            detail="too many voyage uploads; please wait and retry",
            headers={"Retry-After": str(settings.rate_limit_window_seconds)},
        )


async def enforce_pipeline_quota(
    principal: Annotated[Principal, Depends(get_current_user)],
) -> Principal:
    """Per-account (and global) quota on the expensive Anthropic-backed actions.

    Counts the caller's prior cost actions in the rolling window from the audit
    log (so the limit survives restarts and is shared across instances, unlike
    the per-IP in-memory guard above). The shared demo identity gets the tighter
    demo limit. A global daily ceiling caps total spend across all accounts.
    Returns the principal so routes can reuse it without re-declaring the dep.
    """
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)

    # Global daily budget kill-switch (0 disables).
    if settings.global_pipeline_daily_max > 0:
        total = await audit.count_actions_since(
            _sessionmaker,
            actions=audit.COST_ACTIONS,
            since=now - timedelta(days=1),
        )
        if total >= settings.global_pipeline_daily_max:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "global_quota_reached",
                    "message": "The service is at capacity for today. Please try again tomorrow.",
                },
                headers={"Retry-After": "3600"},
            )

    is_demo = principal.id == DEV_USER_ID
    limit = (
        settings.demo_pipeline_max if is_demo else settings.per_account_pipeline_max
    )
    if limit > 0:
        window = settings.per_account_pipeline_window_seconds
        used = await audit.count_actions_since(
            _sessionmaker,
            actions=audit.COST_ACTIONS,
            since=now - timedelta(seconds=window),
            actor_sub=principal.id,
        )
        if used >= limit:
            minutes = max(1, window // 60)
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "account_quota_reached",
                    "message": (
                        f"You have reached the limit of {limit} runs per "
                        f"{minutes} minutes. Please try again later."
                    ),
                },
                headers={"Retry-After": str(window)},
            )
    return principal


# Per-caller rate limit for invitation mint (security hardening). A
# compromised admin token could otherwise mint thousands of invites; the
# limit is loose enough to support paste-batch invites and tight enough
# to bound the damage.
invitation_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.invitation_rate_limit_max,
    window_seconds=settings.invitation_rate_limit_window_seconds,
)


async def enforce_invitation_rate_limit(request: Request) -> None:
    if not invitation_rate_limiter.allow(client_key(request)):
        raise HTTPException(
            status_code=429,
            detail="too many invitations; please wait and retry",
            headers={
                "Retry-After": str(settings.invitation_rate_limit_window_seconds)
            },
        )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# First-party auth: email/password accounts (real multi-user identity).
#
# /auth/signup and /auth/login mint a short HS256 session token the web app
# stores in its httpOnly cookie and replays as the Bearer header. A brute-force
# guard caps attempts per client; the credential check itself is constant-time.
# ---------------------------------------------------------------------------


auth_rate_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)


async def enforce_auth_rate_limit(request: Request) -> None:
    if not auth_rate_limiter.allow(client_key(request)):
        raise HTTPException(
            status_code=429,
            detail="too many attempts; please wait and retry",
            headers={"Retry-After": "60"},
        )


@app.post("/auth/signup", dependencies=[Depends(enforce_auth_rate_limit)])
async def auth_signup(req: accounts.SignupRequest) -> accounts.AuthResponse:
    """Invite-only account creation (cost control).

    A new account is allowed only when the request carries EITHER:
      * a valid, still-pending invitation token whose email matches the signup
        email (the normal path; the invite is consumed so the new user lands as
        a workspace member), OR
      * the configured SIGNUP_BOOTSTRAP_CODE (founder onboarding; mints a
        standalone account with just its personal workspace).

    Anything else is 403. 409 if the email is already registered.
    """
    email_lower = req.email.strip().lower()
    invite_token = (req.invite_token or "").strip()
    bootstrap_code = (req.bootstrap_code or "").strip()

    async with _sessionmaker() as session:
        invitation = None
        if invite_token:
            invitation = await workspaces.get_pending_invitation(
                session, token=invite_token
            )
            if invitation is None:
                raise HTTPException(
                    status_code=410,
                    detail={
                        "code": "invitation_invalid",
                        "message": "This invitation has expired or already been used. Ask for a fresh one.",
                    },
                )
            if invitation.email.strip().lower() != email_lower:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "invitation_email_mismatch",
                        "message": "Use the email address this invitation was sent to.",
                    },
                )
        else:
            code = settings.signup_bootstrap_code
            if not (code and bootstrap_code and bootstrap_code == code):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "signup_invite_only",
                        "message": "Signups are invite-only. Open your invitation link, or enter a valid access code.",
                    },
                )

        try:
            user = await accounts.create_account(
                session, email=req.email, password=req.password, name=req.name
            )
        except accounts.AccountError as exc:
            await session.rollback()
            status = 409 if exc.code == "email_taken" else 400
            raise HTTPException(
                status_code=status,
                detail={"code": exc.code, "message": exc.message},
            )
        sub, email, name = user.id, user.email, user.name

        if invitation is not None:
            # Consume the invite so the new user joins the inviting workspace
            # immediately (the /invite page accept becomes an idempotent no-op).
            await workspaces.accept_invitation(
                session, token=invite_token, acceptor_sub=sub
            )
        else:
            # Bootstrap account: just its own personal workspace.
            await workspaces.ensure_personal_workspace(
                session, user_sub=sub, display_name=name or email
            )
        await audit.record(
            session,
            actor_sub=sub,
            action="auth.signup",
            target_type="user",
            target_id=sub,
            payload={"via": "invite" if invitation is not None else "bootstrap"},
        )
        await session.commit()

    token = accounts.issue_app_token(sub=sub, email=email, name=name)
    return accounts.AuthResponse(
        token=token, user=accounts.AuthUser(sub=sub, email=email, name=name)
    )


DEMO_USER_NAME = "Laytimely Demo"


@app.post("/auth/demo", dependencies=[Depends(enforce_auth_rate_limit)])
async def auth_demo() -> accounts.AuthResponse:
    """One-click demo. Returns a session token for a shared demo identity that
    owns the seeded Rotterdam case data, so a prospect can explore a fully
    populated app without signing up. The demo identity, its workspace, and its
    seed cases are provisioned lazily here so the endpoint works even on a
    non-empty production database (where the startup seed-if-empty never ran)."""
    await store.ensure_user(DEV_USER_ID, DEV_USER_EMAIL)
    async with _sessionmaker() as session:
        wid, created = await workspaces.ensure_personal_workspace(
            session, user_sub=DEV_USER_ID, display_name=DEMO_USER_NAME
        )
        # Force the demo workspace name even if the row predates the rename, so
        # the members/invitations pages never surface a stale "dev@..." label.
        ws_row = await session.get(_WorkspaceRow, wid)
        if ws_row is not None and ws_row.name != DEMO_USER_NAME:
            ws_row.name = DEMO_USER_NAME
            created = True
        if created:
            await session.commit()
    if not await store.list(owner_user_id=DEV_USER_ID):
        for state in seed_voyages():
            await store.save(state, owner_user_id=DEV_USER_ID)
    async with _sessionmaker() as session:
        await audit.record(
            session,
            actor_sub=DEV_USER_ID,
            action="auth.demo",
            target_type="user",
            target_id=DEV_USER_ID,
        )
        await session.commit()
    token = accounts.issue_app_token(
        sub=DEV_USER_ID, email=DEV_USER_EMAIL, name=DEMO_USER_NAME
    )
    return accounts.AuthResponse(
        token=token,
        user=accounts.AuthUser(
            sub=DEV_USER_ID, email=DEV_USER_EMAIL, name=DEMO_USER_NAME
        ),
    )


@app.post("/auth/login", dependencies=[Depends(enforce_auth_rate_limit)])
async def auth_login(req: accounts.LoginRequest) -> accounts.AuthResponse:
    """Verify credentials and return a session token. 401 on bad credentials.
    Ensures the account has its personal workspace (older accounts, safety)."""
    async with _sessionmaker() as session:
        try:
            user = await accounts.authenticate(
                session, email=req.email, password=req.password
            )
        except accounts.AccountError as exc:
            # Record the failed attempt (no actor; the attempted email is the
            # target) so the admin dashboard can spot brute-force patterns.
            await audit.record(
                session,
                actor_sub=None,
                action="auth.login_failed",
                target_type="user",
                target_id=req.email.strip().lower()[:120],
            )
            await session.commit()
            raise HTTPException(
                status_code=401,
                detail={"code": exc.code, "message": exc.message},
            )
        sub, email, name = user.id, user.email, user.name
        _wid, created = await workspaces.ensure_personal_workspace(
            session, user_sub=sub, display_name=name or email
        )
        await audit.record(
            session,
            actor_sub=sub,
            action="auth.login",
            target_type="user",
            target_id=sub,
        )
        await session.commit()
    token = accounts.issue_app_token(sub=sub, email=email, name=name)
    return accounts.AuthResponse(
        token=token, user=accounts.AuthUser(sub=sub, email=email, name=name)
    )


@app.get("/me")
async def me(user: Annotated[Principal, Depends(get_current_user)]) -> Principal:
    """The current authenticated principal (id + email)."""
    return user


# ---------------------------------------------------------------------------
# Admin observability (gated to the ADMIN_EMAILS allowlist from Doppler).
#
# Read-only usage + auth rollups for the founders' dashboard. The allowlist is
# checked server-side on every route, so nothing in the UI can bypass it.
# ---------------------------------------------------------------------------


async def require_admin(
    principal: Annotated[Principal, Depends(get_current_user)],
) -> Principal:
    email = (principal.email or "").strip().lower()
    if not settings.admin_emails or email not in settings.admin_emails:
        raise HTTPException(status_code=403, detail="admin access required")
    return principal


@app.get("/admin/overview")
async def admin_overview(
    principal: Annotated[Principal, Depends(require_admin)],
    days: int = 30,
) -> admin_mod.AdminOverview:
    """Aggregated token usage + auth activity over the last ``days`` (1-365)."""
    days = max(1, min(days, 365))
    async with _sessionmaker() as session:
        await audit.record(
            session,
            actor_sub=principal.id,
            action="admin.view",
            target_type="admin",
            target_id="overview",
        )
        await session.commit()
    return await admin_mod.overview(_sessionmaker, days=days)


@app.get("/admin/events")
async def admin_events(
    _principal: Annotated[Principal, Depends(require_admin)],
    limit: int = 50,
) -> list[admin_mod.AuthEvent]:
    """Most recent sign-ups / sign-ins / failed logins / demo starts."""
    limit = max(1, min(limit, 200))
    return await admin_mod.recent_auth_events(_sessionmaker, limit=limit)


class _MyWorkspaceEntry(BaseModel):
    """One row of GET /me/workspaces: a workspace + the caller's role in it.

    Used by the W8 workspace switcher chip and the W8 /settings/members
    page to know which workspace context they are rendering.
    """

    workspace: workspaces.Workspace
    role: workspaces.Role


@app.get("/me/workspaces")
async def list_my_workspaces(
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[_MyWorkspaceEntry]:
    """Every workspace the caller is a member of, with their role.

    Idempotently ensures the caller has a personal workspace before
    listing, so a brand-new user always sees at least one row (the
    invariant the W8 switcher relies on)."""
    async with _sessionmaker() as session:
        _wid, created = await workspaces.ensure_personal_workspace(
            session, user_sub=user.id, display_name=user.email
        )
        # Skip the commit on the hot read path: the workspace already
        # existed and ``ensure_personal_workspace`` made no writes. Only
        # commit when we actually inserted a fresh row.
        if created:
            await session.commit()
        rows = await workspaces.list_memberships_for_user(session, user_sub=user.id)
    return [
        _MyWorkspaceEntry(
            workspace=workspaces.Workspace(id=ws.id, name=ws.name, plan=ws.plan),
            role=role,
        )
        for ws, role in rows
    ]


# ---------------------------------------------------------------------------
# Workspaces (W7/§2.1)
#
# Foundation only: every authed call ensures the caller has a personal
# workspace (so the data model is consistent). The /workspaces routes ship the
# invitation contract; the workspace switcher UI lands with the WORKSPACES_UI
# flag.
# ---------------------------------------------------------------------------


_require_admin = workspaces.require_workspace_role("admin", _sessionmaker)


@app.get("/workspaces/{workspace_id}/members")
async def list_workspace_members(
    workspace_id: str,
    _principal: Annotated[Principal, Depends(_require_admin)],
) -> list[workspaces.Member]:
    """Admin-only: list the workspace's members, each joined to its user row
    so the UI can show an email/name rather than an opaque id."""
    from sqlalchemy import select as _select
    from .db.models import MembershipRow as _MembershipRow, User as _User

    async with _sessionmaker() as session:
        result = await session.execute(
            _select(_MembershipRow, _User)
            .join(_User, _User.id == _MembershipRow.user_sub, isouter=True)
            .where(_MembershipRow.workspace_id == workspace_id)
            .order_by(_MembershipRow.accepted_at)
        )
        rows = result.all()
    return [
        workspaces.Member(
            user_sub=mem.user_sub,
            role=mem.role,  # type: ignore[arg-type]
            email=(user.email if user is not None else None),
            name=(user.name if user is not None else None),
        )
        for (mem, user) in rows
    ]


_MEMBER_REMOVE_STATUS: dict[str, int] = {
    "not_found": 404,
    "last_owner": 409,
}


@app.delete("/workspaces/{workspace_id}/members/{user_sub}", status_code=204)
async def remove_workspace_member(
    workspace_id: str,
    user_sub: str,
    principal: Annotated[Principal, Depends(_require_admin)],
) -> Response:
    """Admin-only: drop a single membership row (W8).

    Refuses with 409 ``last_owner`` when the target is the only owner; the
    admin must promote another member to owner first. The caller can remove
    themselves if and only if another owner exists, which lets a departing
    admin clean up without orphaning the workspace.
    """
    async with _sessionmaker() as session:
        try:
            removed = await workspaces.remove_member(
                session, workspace_id=workspace_id, user_sub=user_sub
            )
        except workspaces.MemberRemoveError as exc:
            status = _MEMBER_REMOVE_STATUS.get(exc.code, 400)
            await session.rollback()
            raise HTTPException(
                status_code=status,
                detail={"code": exc.code, "message": exc.message},
            ) from exc
        await session.commit()
    await _audit(
        principal.id,
        "workspace.member_remove",
        "membership",
        f"{workspace_id}:{user_sub}",
        {
            "workspace_id": workspace_id,
            "removed_user_sub": user_sub,
            "prior_role": removed.role,
        },
    )
    return Response(status_code=204)


class _ChangeRoleRequest(BaseModel):
    """Body for PATCH /workspaces/{id}/members/{sub} (review #11)."""

    role: workspaces.Role


@app.patch("/workspaces/{workspace_id}/members/{user_sub}")
async def change_workspace_member_role(
    workspace_id: str,
    user_sub: str,
    body: _ChangeRoleRequest,
    principal: Annotated[Principal, Depends(_require_admin)],
) -> workspaces.Member:
    """Admin-only: promote or demote a member (review #11).

    Reuses the same closed error vocabulary as remove-member: 404 for
    missing membership, 409 ``last_owner`` for demoting the only owner.
    Writes a ``workspace.member_remove`` audit row with the prior role
    so the change is reconstructable from the audit log alone — using
    the existing action keeps the audit vocabulary closed without a
    migration.
    """
    async with _sessionmaker() as session:
        try:
            updated = await workspaces.change_member_role(
                session,
                workspace_id=workspace_id,
                user_sub=user_sub,
                new_role=body.role,
            )
        except workspaces.MemberRemoveError as exc:
            status = _MEMBER_REMOVE_STATUS.get(exc.code, 400)
            await session.rollback()
            raise HTTPException(
                status_code=status,
                detail={"code": exc.code, "message": exc.message},
            ) from exc
        prior_role = updated.role if updated.role == body.role else None
        await session.commit()
    await _audit(
        principal.id,
        "workspace.member_remove",
        "membership",
        f"{workspace_id}:{user_sub}",
        {
            "workspace_id": workspace_id,
            "target_user_sub": user_sub,
            "new_role": body.role,
            "kind": "role_change",
        },
    )
    return workspaces.Member(user_sub=user_sub, role=body.role)


@app.post(
    "/workspaces/{workspace_id}/invitations/{invitation_id}/revoke",
    status_code=204,
)
async def revoke_workspace_invitation(
    workspace_id: str,
    invitation_id: int,
    principal: Annotated[Principal, Depends(_require_admin)],
) -> Response:
    """Admin-only: revoke a pending invitation (review #10).

    410 when the row does not belong to this workspace, has been
    accepted, or is already revoked. Idempotent on a successful first
    revoke (subsequent calls 410 because revoked_at is set).
    """
    async with _sessionmaker() as session:
        row = await workspaces.revoke_invitation(
            session,
            invitation_id=invitation_id,
            workspace_id=workspace_id,
        )
        if row is None:
            raise HTTPException(
                status_code=410,
                detail={
                    "code": "invitation_invalid",
                    "message": "invitation not found, accepted, or already revoked",
                },
            )
        await session.commit()
    await _audit(
        principal.id,
        "workspace.invite",
        "invitation",
        str(invitation_id),
        {
            "workspace_id": workspace_id,
            "kind": "revoke",
        },
    )
    return Response(status_code=204)


@app.get("/workspaces/{workspace_id}/invitations")
async def list_workspace_invitations(
    workspace_id: str,
    _principal: Annotated[Principal, Depends(_require_admin)],
) -> list[workspaces.Invitation]:
    """Admin-only: list pending invitations for a workspace (W9).

    "Pending" excludes accepted, revoked, and expired rows. Newest first.
    The admin sees the canonical row including the ``token`` so they can
    copy the accept link out-of-band; SES delivery of the invite is a
    separate path tracked under the SES setup checklist.
    """
    async with _sessionmaker() as session:
        rows = await workspaces.list_pending_invitations(
            session, workspace_id=workspace_id
        )
    return [workspaces.to_invitation(row) for row in rows]


@app.get("/workspaces/{workspace_id}/inbox-address")
async def get_workspace_inbox_address(
    workspace_id: str,
    _principal: Annotated[Principal, Depends(_require_admin)],
) -> InboxAddressResponse:
    """The forward-to address for the workspace's email-in surface (W7,
    notes/architecture_weeks_5_to_8.md §2.3 + W7 frontend brief).

    Computed deterministically from the workspace id + the ``INBOX_DOMAIN``
    setting; no row to read. Admin-only because the address is the inbound
    write surface for the workspace; regular members do not manage it.
    """
    return InboxAddressResponse(
        address=workspaces.inbox_address(workspace_id, settings.inbox_domain),
    )


@app.post(
    "/workspaces/{workspace_id}/invitations",
    status_code=201,
    dependencies=[Depends(enforce_invitation_rate_limit)],
)
async def create_workspace_invitation(
    workspace_id: str,
    body: workspaces.CreateInvitationRequest,
    principal: Annotated[Principal, Depends(_require_admin)],
) -> workspaces.Invitation:
    """Admin-only: mint an invitation token + send the SES invitation email
    (review #12). When ``settings.email_send_live`` is off, the SES adapter
    returns a synthetic sandbox result and the route still 201s — the admin
    sees the row, can copy the accept link manually, and the audit log
    records the sandbox flag for post-deploy verification.

    SES failures do NOT roll back the invitation row: a transient SES error
    that prevented the email shouldn't prevent the admin from re-sharing
    the accept link manually. The failure is captured in the audit
    payload's ``email_error_code``.
    """
    async with _sessionmaker() as session:
        row = await workspaces.create_invitation(
            session,
            workspace_id=workspace_id,
            email=str(body.email),
            role=body.role,
            invited_by_sub=principal.id,
        )
        # Read the workspace name in the same session (avoids an extra
        # query and N+1 if the route grows).
        ws = await session.get(_WorkspaceRow, workspace_id)
        workspace_name = ws.name if ws is not None else workspace_id
        await session.commit()

    accept_url = f"{settings.invitation_base_url}/invite/{row.token}"
    email_payload: dict = {
        "workspace_id": workspace_id,
        "role": body.role,
        "invitation_id": row.id,
    }
    try:
        result = await invitation_email.send_invitation_email(
            recipient=row.email,
            workspace_name=workspace_name,
            role=body.role,
            accept_url=accept_url,
            invited_by_email=principal.email,
        )
        email_payload["email_sandbox"] = result.sandbox
        email_payload["email_message_id"] = result.ses_message_id
    except EmailSendError as exc:
        logger.warning(
            "invitation email send failed for %s: %s", row.email, exc.message,
        )
        email_payload["email_error_code"] = exc.code.value

    await _audit(
        principal.id,
        "workspace.invite",
        "invitation",
        str(row.id),
        email_payload,
    )
    return workspaces.to_invitation(row)


@app.post("/invitations/{token}/accept")
async def accept_workspace_invitation(
    token: str,
    principal: Annotated[Principal, Depends(get_current_user)],
) -> workspaces.Invitation:
    """Public-ish accept: the caller must be authed, but they do not yet need
    to be a member of the workspace (that is the point of the invite). 410
    for expired / revoked / already-accepted tokens."""
    async with _sessionmaker() as session:
        row = await workspaces.accept_invitation(
            session, token=token, acceptor_sub=principal.id
        )
        if row is None:
            raise HTTPException(status_code=410, detail="invitation not active")
        await session.commit()
    await _audit(
        principal.id,
        "workspace.accept",
        "invitation",
        str(row.id),
        {"workspace_id": row.workspace_id, "role": row.role},
    )
    return workspaces.to_invitation(row)


@app.get("/audit")
async def list_audit_events(
    user: Annotated[Principal, Depends(get_current_user)],
    limit: int = 100,
) -> list[AuditEvent]:
    """Recent audit events for the caller (notes/architecture_weeks_5_to_8.md §2.2).

    Workspace-admin view (all events for a workspace) lands with §2.1. Limit
    is clamped to a sane ceiling so a malicious caller cannot stream the
    whole table.
    """
    limit = max(1, min(limit, 500))
    return await audit.list_for_actor(_sessionmaker, user.id, limit=limit)


@app.get("/voyages")
async def list_voyages(
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[VoyageSummary]:
    """Return the caller's voyages as lightweight summaries, newest-first."""
    return await store.list(user.id)


@app.get("/vessels")
async def list_vessels(
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[VesselSummary]:
    """Return the caller's voyages grouped by vessel, newest-active first."""
    return await store.list_vessels(user.id)


@app.post(
    "/voyages",
    status_code=201,
    dependencies=[
        Depends(enforce_voyage_rate_limit),
        Depends(enforce_pipeline_quota),
    ],
)
async def create_voyage(
    cp: UploadFile,
    nor: UploadFile,
    sof: UploadFile,
    perspective: Annotated[Perspective, Form()],
    user: Annotated[Principal, Depends(get_current_user)],
) -> dict[str, str]:
    """Accept three voyage PDFs, kick off the pipeline in the background, and
    return the voyage_id immediately. The pipeline writes each stage to the store
    so the frontend's GET poll sees progress (uploaded -> ... -> done | error).
    """
    files = {
        "cp": await validate_and_read(cp, role="cp"),
        "nor": await validate_and_read(nor, role="nor"),
        "sof": await validate_and_read(sof, role="sof"),
    }

    voyage_id = f"v_{uuid.uuid4().hex[:12]}"
    # Ensure the owner row exists (FK), then seed the initial state synchronously
    # with ownership so a fast follow-up GET never 404s and is owner-scoped.
    await store.ensure_user(user.id, user.email)
    await store.save(
        VoyageState(voyage_id=voyage_id, perspective=perspective, stage="uploaded"),
        owner_user_id=user.id,
    )
    # Persist the uploaded PDFs to object storage and record their metadata.
    documents: list[StoredDocument] = []
    for role, data in files.items():
        key = build_key(voyage_id, role, settings.s3_prefix)
        await object_store.put(key, data, "application/pdf")
        documents.append(
            StoredDocument(
                role=role,
                object_key=key,
                content_type="application/pdf",
                size_bytes=len(data),
            )
        )
    await store.record_documents(voyage_id, documents)
    # Attribute the pipeline's model usage to this caller + voyage. create_task
    # snapshots the current context, so the background pipeline inherits this.
    token_usage.set_context(actor_sub=user.id, voyage_id=voyage_id)
    # Fire-and-forget the pipeline; hold a strong reference until it completes.
    task = asyncio.create_task(_run_pipeline_bg(voyage_id, perspective, files))
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)

    await _audit(
        user.id,
        "voyage.create",
        "voyage",
        voyage_id,
        {"perspective": perspective},
    )
    return {"voyage_id": voyage_id}


@app.get("/voyages/{voyage_id}")
async def get_voyage(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> VoyageState:
    """Return the caller's VoyageState (the frontend polls this)."""
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    return state


@app.delete("/voyages/{voyage_id}", status_code=204)
async def delete_voyage(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> None:
    """Delete one of the caller's voyages. 404 if it is missing or not theirs."""
    if not await store.delete(voyage_id, user.id):
        raise HTTPException(status_code=404, detail="voyage not found")
    await _audit(user.id, "voyage.delete", "voyage", voyage_id, {})


@app.get("/voyages/{voyage_id}/documents")
async def list_voyage_documents(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[VoyageDocumentInfo]:
    """Metadata for the caller's uploaded source PDFs (role, type, size)."""
    if await store.load(voyage_id, user.id) is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    docs = await store.list_documents(voyage_id, user.id)
    return [
        VoyageDocumentInfo(
            role=d.role, content_type=d.content_type, size_bytes=d.size_bytes
        )
        for d in docs
    ]


@app.get("/voyages/{voyage_id}/documents/{role}")
async def download_voyage_document(
    voyage_id: str,
    role: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> Response:
    """Stream one of the caller's uploaded PDFs back from object storage."""
    docs = await store.list_documents(voyage_id, user.id)
    match = next((d for d in docs if d.role == role), None)
    if match is None:
        raise HTTPException(status_code=404, detail="document not found")
    data = await object_store.get(match.object_key)
    if data is None:
        raise HTTPException(status_code=404, detail="document bytes not found")
    return Response(content=data, media_type=match.content_type)


# Allowed human-driven lifecycle transitions once the pipeline is done. The
# claim then moves through negotiation: send it (-> pending), the charterer
# settles (-> settled) or rejects (-> rejected), and a rejected claim is revised
# and resent (-> pending). The pipeline stages (uploaded..drafting) are not in
# here — they advance on their own inside pipeline.run.
_NEXT_STAGES: dict[str, set[str]] = {
    "done": {"pending"},
    "pending": {"settled", "rejected"},
    "rejected": {"pending"},
}


@app.post("/voyages/{voyage_id}/status")
async def set_voyage_status(
    voyage_id: str,
    body: StatusUpdate,
    user: Annotated[Principal, Depends(get_current_user)],
) -> VoyageState:
    """Advance a voyage through the negotiation lifecycle (notes: status chips).

    Only the transitions in ``_NEXT_STAGES`` are permitted; anything else is a
    409 so the UI can't drive the claim into an inconsistent state.
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")

    allowed = _NEXT_STAGES.get(state.stage, set())
    if body.stage not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"cannot move from '{state.stage}' to '{body.stage}'",
        )

    updated = await store.patch(voyage_id, stage=body.stage)
    assert updated is not None  # load() above proved it exists
    await _audit(
        user.id,
        "voyage.status_change",
        "voyage",
        voyage_id,
        {"from_stage": state.stage, "to_stage": body.stage},
    )
    return updated


@app.post(
    "/voyages/{voyage_id}/revise",
    dependencies=[Depends(enforce_pipeline_quota)],
)
async def revise_voyage(
    voyage_id: str,
    body: ReviseRequest,
    user: Annotated[Principal, Depends(get_current_user)],
) -> ReviseResponse:
    """Inline-revise a letter/narrative segment (notes/13-inline-revision.md).

    The rewrite is validated server-side: if it changed a monetary value or
    dropped a CP clause / SoF event reference, it is rejected with HTTP 422 and
    the safety report so the UI can surface why.
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")

    blocked, response = await reviser.revise(body, state)
    if blocked:
        raise HTTPException(status_code=422, detail=response.model_dump())
    return response


@app.post(
    "/voyages/{voyage_id}/revise/apply",
    dependencies=[Depends(enforce_pipeline_quota)],
)
async def apply_revision(
    voyage_id: str,
    body: ApplyRevisionRequest,
    user: Annotated[Principal, Depends(get_current_user)],
) -> VoyageState:
    """Persist accepted revisions into the stored packet so they survive a
    reload and flow into the PDF export. The safety gate runs again here: a
    rewrite that changed a monetary value or dropped a clause/event reference is
    rejected (422) and never reaches the store.
    """
    state = await store.load(voyage_id, user.id)
    if state is None or state.packet is None:
        raise HTTPException(status_code=404, detail="voyage not found")

    new_packet, report, error = reviser.apply_revisions(
        state.packet, body.surface, body.edits
    )
    if new_packet is None:
        raise HTTPException(
            status_code=422,
            detail={"safety": report.model_dump(), "error": error},
        )

    updated = await store.patch(voyage_id, packet=new_packet)
    assert updated is not None  # load() above proved it exists
    await _audit(user.id, "voyage.revise_apply", "voyage", voyage_id, {})
    return updated


@app.post(
    "/voyages/{voyage_id}/rebut",
    dependencies=[Depends(enforce_pipeline_quota)],
)
async def rebut_voyage(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> RebuttalPacket:
    """Produce the charterer's rebuttal packet for one of the caller's voyages.

    Numbers are deterministic — winning the contested rows drops the quantum
    by ``contested_eur`` (e.g. the Rotterdam demo: 84,375.00 -> 76,875.00).
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    if state.extraction is None or state.laytime is None or state.dispute is None:
        raise HTTPException(
            status_code=409, detail="voyage is not ready for rebuttal"
        )
    rebuttal = await defense.build_rebuttal_packet(state)
    await _audit(user.id, "voyage.rebuttal", "voyage", voyage_id, {})
    return rebuttal


_EMAIL_ERROR_STATUS: dict[EmailErrorCode, int] = {
    EmailErrorCode.SANDBOX_UNVERIFIED: 422,
    EmailErrorCode.THROTTLED: 429,
    EmailErrorCode.REJECTED: 422,
    EmailErrorCode.TRANSPORT: 502,
    EmailErrorCode.NOT_CONFIGURED: 503,
}


@app.post("/voyages/{voyage_id}/letter/email")
async def email_claim_letter(
    voyage_id: str,
    body: LetterEmailRequest,
    user: Annotated[Principal, Depends(get_current_user)],
) -> SesSendResult:
    """Send the claim letter via SES (notes/architecture_weeks_5_to_8.md §1.3).

    When ``settings.email_send_live`` is off the route runs end-to-end against
    the sandbox path (audit row + 200 with ``sandbox=true``) so the surface
    is exercised without an SES identity. When live, errors are translated to
    a stable HTTP status via the ``EmailErrorCode`` enum.

    Note: PDF attachment upload is a stretch (multipart form variant of this
    route) and will land in a follow-up PR; the v0.1 surface emails the
    Markdown letter body inline.
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    if state.packet is None:
        raise HTTPException(status_code=409, detail="voyage is not ready to email")
    try:
        result = await send_claim_letter(state, body)
    except EmailSendError as exc:
        status = _EMAIL_ERROR_STATUS.get(exc.code, 502)
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc
    await _audit(
        user.id,
        "voyage.letter_email",
        "voyage",
        voyage_id,
        {
            "recipients_to": list(body.to),
            "recipients_cc": list(body.cc),
            "recipients_bcc": list(body.bcc),
            "sandbox": result.sandbox,
            "ses_message_id": result.ses_message_id,
        },
    )
    return result


_INBOUND_ERROR_STATUS: dict[InboundErrorCode, int] = {
    InboundErrorCode.BAD_SIGNATURE: 401,
    InboundErrorCode.BAD_PAYLOAD: 400,
    InboundErrorCode.NO_PDF_ATTACHMENT: 400,
    InboundErrorCode.OVERSIZE: 413,
    InboundErrorCode.DISALLOWED_TYPE: 415,
    InboundErrorCode.VIRUS_DETECTED: 422,
}


@app.post("/voyages/from-email", status_code=202)
async def voyages_from_email(
    request: Request,
    x_laytimely_inbound_signature: Annotated[str | None, Header()] = None,
    x_laytimely_av_scanned: Annotated[str | None, Header()] = None,
    x_laytimely_av_clean: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Inbound email ingestion (notes/architecture_weeks_5_to_8.md §2.3).

    The SES → S3 → Lambda hop forwards each scanned message here. The
    boundary is one HMAC-SHA256 header verified in constant time; without the
    matching signature the route 401s. AV flags come from headers the Lambda
    sets; v0.1 trusts those (a follow-up moves a ClamAV pass in-process).

    On success the route returns 202 with the voyage id the message was
    attached to ("matched": "existing" | "new"). The pipeline run is
    fire-and-forget like the regular POST /voyages.
    """
    raw = await request.body()
    try:
        verify_signature(
            settings.email_in_shared_secret, raw, x_laytimely_inbound_signature
        )
    except InboundError as exc:
        raise HTTPException(
            status_code=_INBOUND_ERROR_STATUS[exc.code],
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc

    av_scanned = (x_laytimely_av_scanned or "").lower() in {"1", "true", "yes"}
    av_clean = (x_laytimely_av_clean or "").lower() in {"1", "true", "yes"}

    try:
        message = parse_message(raw, av_scanned=av_scanned, av_clean=av_clean)
    except InboundError as exc:
        raise HTTPException(
            status_code=_INBOUND_ERROR_STATUS[exc.code],
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc

    existing_id = match_voyage(message)
    perspective: Perspective = "owner"  # inbound mail defaults to owner-side

    if existing_id is not None:
        # Existing voyage: append the inbound attachments as documents and
        # log the event; no new pipeline run today.
        state = await store.load(existing_id, DEV_USER_ID)
        if state is not None:
            for att in message.attachments:
                key = build_key(existing_id, f"inbox-{att.filename}", settings.s3_prefix)
                await object_store.put(key, att.data, "application/pdf")
                await store.record_documents(
                    existing_id,
                    [
                        StoredDocument(
                            role="inbox",
                            object_key=key,
                            content_type="application/pdf",
                            size_bytes=att.size_bytes,
                        )
                    ],
                )
            await _audit(
                DEV_USER_ID,
                "voyage.from_email",
                "voyage",
                existing_id,
                {"source": message.sender, "voyage_id": existing_id},
            )
            return {"voyage_id": existing_id, "matched": "existing"}

    # No match: open a new voyage. Same shape as POST /voyages: seed the
    # state, persist the documents, kick the pipeline off-thread. Because
    # inbound mail does not pre-classify attachments, we map the first three
    # PDFs onto cp/nor/sof in order; a smarter classifier lands later.
    if len(message.attachments) < 3:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INBOUND_INCOMPLETE",
                "message": (
                    "new voyages need three PDFs (cp, nor, sof); "
                    f"received {len(message.attachments)}"
                ),
            },
        )

    voyage_id = f"v_{uuid.uuid4().hex[:12]}"
    await store.ensure_user(DEV_USER_ID, DEV_USER_EMAIL)
    await store.save(
        VoyageState(voyage_id=voyage_id, perspective=perspective, stage="uploaded"),
        owner_user_id=DEV_USER_ID,
    )
    roles = ("cp", "nor", "sof")
    files: dict[str, bytes] = {}
    documents: list[StoredDocument] = []
    for role, attachment in zip(roles, message.attachments[:3]):
        files[role] = attachment.data
        key = build_key(voyage_id, role, settings.s3_prefix)
        await object_store.put(key, attachment.data, "application/pdf")
        documents.append(
            StoredDocument(
                role=role,
                object_key=key,
                content_type="application/pdf",
                size_bytes=attachment.size_bytes,
            )
        )
    await store.record_documents(voyage_id, documents)
    task = asyncio.create_task(_run_pipeline_bg(voyage_id, perspective, files))
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)

    await _audit(
        DEV_USER_ID,
        "voyage.from_email",
        "voyage",
        voyage_id,
        {"source": message.sender, "perspective": perspective},
    )
    return {"voyage_id": voyage_id, "matched": "new"}


@app.get("/voyages/{voyage_id}/laytime.xlsx")
async def export_laytime_xlsx(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> Response:
    """Render the laytime ledger + summary + letter to a three-sheet workbook.

    Spec: notes/architecture_weeks_5_to_8.md §1.1. Workbook shape is fixed and
    snapshot-tested against the Rotterdam fixture so the public API consumer
    can rely on it (sheet names, cell coordinates, the canonical quantum at
    Summary!B7). 409 when the pipeline has not produced laytime yet.
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    if state.extraction is None or state.laytime is None:
        raise HTTPException(status_code=409, detail="voyage is not ready for export")

    # Render off-thread so the event loop never blocks on a large workbook.
    workbook_bytes = await asyncio.to_thread(
        excel_export.render_laytime_workbook, state
    )
    vessel = (
        state.extraction.charter_party.vessel_name.replace(" ", "_")
        if state.extraction
        else "voyage"
    )
    filename = f"laytime-{vessel}-{voyage_id}.xlsx"
    return Response(
        content=workbook_bytes,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/voyages/{voyage_id}/evidence")
async def list_voyage_evidence(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[EvidenceItem]:
    """Externally-sourced evidence for the caller's flagged events (lazy-gathered
    on first read and cached). Currently weather observations for weather-
    stoppage events; other tools plug in behind the same endpoint."""
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    cached = await store.list_evidence(voyage_id, user.id)
    if cached:
        return cached
    if state.extraction is None or state.dispute is None:
        raise HTTPException(
            status_code=409, detail="voyage is not ready for evidence gathering"
        )
    bundle = await researcher.gather_evidence(state.extraction, state.dispute)
    if bundle.items:
        await store.record_evidence(voyage_id, bundle.items)
    return bundle.items


@app.get("/voyages/{voyage_id}/evidence-checklist")
async def get_evidence_checklist(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> EvidenceChecklist:
    """Recipient-facing evidence checklist (W3, notes/architecture_weeks_5_to_8.md §1.4).

    Composes ``evidence_checklist.build_checklist`` against the current voyage
    state: flagged events + uploaded document roles + any cached
    research-agent evidence bundle. ``attached`` per row is deterministic
    here, not model-owned. 409 when no dispute is on the state yet.
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    if state.dispute is None:
        raise HTTPException(
            status_code=409, detail="voyage has no dispute analysis yet"
        )
    docs = await store.list_documents(voyage_id, user.id)
    cached_evidence = await store.list_evidence(voyage_id, user.id)
    bundle = EvidenceBundle(items=cached_evidence) if cached_evidence else None
    return build_evidence_checklist(
        state.dispute.flagged_events,
        voyage_documents=[d.role for d in docs],
        evidence_bundle=bundle,
    )


@app.get("/voyages/{voyage_id}/strengths")
async def get_claim_strengths(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[FlaggedEventStrength]:
    """Per-event sub-score panels (W4, notes/architecture_weeks_5_to_8.md §1.5).

    Composes the four-cell strength panel for each contested event:
      - ``time_bar_risk`` from ``packet.days_until_time_bar`` (deterministic)
      - ``evidence_completeness`` from the per-event checklist rows (deterministic)
      - ``clause_clarity`` + ``counterparty_pushback_risk`` derived from the
        analyst's calibrated ``owner_position_strength`` (v0.1 fallback; v0.2
        replaces this with an extended analyst prompt that emits the two
        words directly, see §1.5 calibration plan).

    404 on unknown voyage; 409 when no dispute is on the state yet.
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    if state.dispute is None:
        raise HTTPException(
            status_code=409, detail="voyage has no dispute analysis yet"
        )
    docs = await store.list_documents(voyage_id, user.id)
    cached_evidence = await store.list_evidence(voyage_id, user.id)
    bundle = EvidenceBundle(items=cached_evidence) if cached_evidence else None
    checklist = build_evidence_checklist(
        state.dispute.flagged_events,
        voyage_documents=[d.role for d in docs],
        evidence_bundle=bundle,
    )
    model_panels = {
        fe.event_id: derive_model_panel_from_event(fe.owner_position_strength)
        for fe in state.dispute.flagged_events
    }
    days = state.packet.days_until_time_bar if state.packet else None
    return build_strength_panels(
        flagged_events=state.dispute.flagged_events,
        model_panels=model_panels,
        days_until_time_bar=days,
        checklist=checklist,
    )


@app.get("/voyages/{voyage_id}/citations")
async def get_voyage_citations(
    voyage_id: str,
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[FlaggedEventCitations]:
    """Verified legal authorities per flagged event (W5,
    notes/architecture_weeks_5_to_8.md §1.6).

    First read: runs the analyst's per-event picker pass against the curated
    corpus, validates with ``legal.verify.validate_authorities``, persists
    the result. Later reads serve the cache. 404 / 409 mirror the other
    sibling routes; an event for which no authority survives verification
    simply does not appear in the response.

    The picker call uses the model; if no ANTHROPIC_API_KEY is present the
    per-event helper returns ``[]`` and the route degrades to an empty list
    rather than 5xx. Production deploys must have the key configured.
    """
    state = await store.load(voyage_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="voyage not found")
    if state.dispute is None:
        raise HTTPException(
            status_code=409, detail="voyage has no dispute analysis yet"
        )

    # Per-event cache check, not all-or-nothing: events whose picker call
    # failed on a prior run (raise / no key) leave a gap in the cache, and a
    # second call must retry only those gaps without re-billing the events
    # that already produced verified rows. The cache surface is the bag of
    # *successful* per-event bundles; "covered" tracks which event_ids we
    # have a row for, so the picker only runs for the rest.
    covered_bundles = await store.list_citations(voyage_id, user.id)
    covered_ids = {bundle.event_id for bundle in covered_bundles}

    to_compute = [
        fe for fe in state.dispute.flagged_events if fe.event_id not in covered_ids
    ]

    async def _safe_pick(event):  # type: ignore[no-untyped-def]
        try:
            return event, await analyst._citations_for_event(event)
        except Exception:  # noqa: BLE001 - boundary handler
            # A picker call failure (no key, network error, model refusal)
            # must not 5xx the whole list. Logged here; the missing event
            # stays uncovered so the next call retries it.
            logger.warning(
                "citations: per-event picker failed for %s/%s",
                voyage_id, event.event_id,
            )
            return event, []

    # Parallelize across events: with N events that's max(latency) instead
    # of sum(latency). For Rotterdam (1 event) no diff; for a 5-event voyage
    # a 3-5x cut to first-render latency.
    fresh_bundles: list[FlaggedEventCitations] = []
    if to_compute:
        results = await asyncio.gather(*(_safe_pick(fe) for fe in to_compute))
        for event, cited in results:
            if cited:
                fresh_bundles.append(
                    FlaggedEventCitations(
                        event_id=event.event_id, cited_authorities=cited
                    )
                )

    if fresh_bundles:
        await store.record_citations(voyage_id, fresh_bundles)
    # Return cached + freshly computed, in the order the dispute analysis
    # emitted the events so the UI's citation numbering stays stable.
    by_id = {b.event_id: b for b in [*covered_bundles, *fresh_bundles]}
    return [
        by_id[fe.event_id]
        for fe in state.dispute.flagged_events
        if fe.event_id in by_id
    ]


async def _run_pipeline_bg(
    voyage_id: str,
    perspective: Perspective,
    files: dict[str, bytes],
) -> None:
    """Run the pipeline in the background.

    The pipeline saves each stage to the store as it advances (live polling) and
    records stage="error" internally on failure. Passing `store` is what enables
    the staged saves. This wrapper is a belt-and-suspenders guard for anything
    that escapes the pipeline's own handler (notes/02-architecture.md §7).
    """
    try:
        await pipeline.run(voyage_id, perspective, files, store)
    except Exception:  # noqa: BLE001 - boundary handler
        # Log the full exception server-side; surface only a generic message to
        # the client so internal types/stack details never reach the polled
        # VoyageState (verbose-error hardening).
        logger.exception("pipeline failed for voyage %s", voyage_id)
        await store.save(
            VoyageState(
                voyage_id=voyage_id,
                perspective=perspective,
                stage="error",
                error=GENERIC_PIPELINE_ERROR,
            )
        )
