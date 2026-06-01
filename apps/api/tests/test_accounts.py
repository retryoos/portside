"""Tests for first-party email/password accounts (real multi-user auth)."""

from __future__ import annotations

import asyncio
from typing import Iterator

import jwt
import pytest
from fastapi.testclient import TestClient

from laytimely_api import accounts, main as main_mod
from tests.conftest import run_wipe


@pytest.fixture
def client() -> Iterator[TestClient]:
    run_wipe()
    with TestClient(main_mod.app) as c:
        yield c
    run_wipe()


# --- password hashing -------------------------------------------------------


def test_password_hash_roundtrip() -> None:
    h = accounts.hash_password("correct horse battery")
    assert h.startswith("pbkdf2_sha256$")
    assert accounts.verify_password("correct horse battery", h)
    assert not accounts.verify_password("wrong", h)


def test_password_hash_is_salted_unique() -> None:
    a = accounts.hash_password("same-password")
    b = accounts.hash_password("same-password")
    assert a != b  # distinct salts
    assert accounts.verify_password("same-password", a)
    assert accounts.verify_password("same-password", b)


def test_verify_password_rejects_malformed_or_empty() -> None:
    assert not accounts.verify_password("x", None)
    assert not accounts.verify_password("x", "")
    assert not accounts.verify_password("x", "not-a-hash")
    assert not accounts.verify_password("x", "bcrypt$1$ab$cd")


# --- session token ----------------------------------------------------------


def test_app_token_roundtrip() -> None:
    tok = accounts.issue_app_token(sub="u1", email="a@b.com", name="A")
    claims = accounts.verify_app_token(tok)
    assert claims["sub"] == "u1"
    assert claims["email"] == "a@b.com"
    assert claims["iss"] == "laytimely"


def test_app_token_rejects_tampered_signature() -> None:
    tok = accounts.issue_app_token(sub="u1", email=None, name=None)
    tampered = tok[:-2] + ("aa" if not tok.endswith("aa") else "bb")
    with pytest.raises(jwt.PyJWTError):
        accounts.verify_app_token(tampered)


# --- account operations (against the shared test DB) ------------------------


def _run(coro):
    return asyncio.run(coro)


async def _create(email: str, password: str, name: str | None = None):
    async with main_mod._sessionmaker() as session:
        user = await accounts.create_account(
            session, email=email, password=password, name=name
        )
        out = (user.id, user.email, user.email_lower, user.name)
        await session.commit()
        return out


def test_create_account_persists_lowercased_key() -> None:
    uid, email, email_lower, name = _run(
        _create("New.User@Acme.com", "password1", "New User")
    )
    assert email == "New.User@Acme.com"  # original casing preserved
    assert email_lower == "new.user@acme.com"  # folded key
    assert name == "New User"
    assert uid


def test_create_account_rejects_duplicate_email() -> None:
    _run(_create("dup@acme.com", "password1"))

    async def _dup():
        async with main_mod._sessionmaker() as session:
            await accounts.create_account(
                session, email="DUP@acme.com", password="password2"
            )

    with pytest.raises(accounts.AccountError) as exc:
        _run(_dup())
    assert exc.value.code == "email_taken"


def test_authenticate_success_and_failure() -> None:
    _run(_create("login@acme.com", "password1", "Loginner"))

    async def _auth(email: str, password: str):
        async with main_mod._sessionmaker() as session:
            return await accounts.authenticate(
                session, email=email, password=password
            )

    user = _run(_auth("Login@acme.com", "password1"))  # case-insensitive
    assert user.email == "login@acme.com"

    with pytest.raises(accounts.AccountError) as exc:
        _run(_auth("login@acme.com", "wrong"))
    assert exc.value.code == "invalid_credentials"

    with pytest.raises(accounts.AccountError) as exc2:
        _run(_auth("nobody@acme.com", "password1"))
    assert exc2.value.code == "invalid_credentials"


# --- HTTP routes ------------------------------------------------------------


_BOOT = {"bootstrap_code": "test-bootstrap"}


def test_signup_then_login_routes(client) -> None:
    s = client.post(
        "/auth/signup",
        json={
            "email": "route@acme.com",
            "password": "password1",
            "name": "R",
            **_BOOT,
        },
    )
    assert s.status_code == 200, s.text
    assert s.json()["token"]
    assert s.json()["user"]["email"] == "route@acme.com"

    # Duplicate signup is a 409 (gate passes, then email_taken).
    dup = client.post(
        "/auth/signup",
        json={"email": "route@acme.com", "password": "password1", **_BOOT},
    )
    assert dup.status_code == 409

    # Login with the right password returns a token; wrong password 401s.
    ok = client.post(
        "/auth/login", json={"email": "route@acme.com", "password": "password1"}
    )
    assert ok.status_code == 200
    assert ok.json()["token"]

    bad = client.post(
        "/auth/login", json={"email": "route@acme.com", "password": "nope"}
    )
    assert bad.status_code == 401


def test_signup_rejects_short_password(client) -> None:
    r = client.post(
        "/auth/signup",
        json={"email": "short@acme.com", "password": "short", **_BOOT},
    )
    assert r.status_code == 422  # pydantic min_length on the request model


def test_demo_route_returns_token(client) -> None:
    r = client.post("/auth/demo")
    assert r.status_code == 200, r.text
    assert r.json()["token"]
    assert r.json()["user"]["name"] == "Laytimely Demo"


# --- invite-only gate -------------------------------------------------------


def test_signup_requires_invite_or_code(client) -> None:
    r = client.post(
        "/auth/signup", json={"email": "no@gate.com", "password": "password1"}
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "signup_invite_only"


def test_signup_with_matching_invite_joins_workspace(client) -> None:
    # dev-user (owner of its personal workspace) mints an invite; a new user
    # signs up with the matching email + token and lands as a member.
    wid = client.get("/me/workspaces").json()[0]["workspace"]["id"]
    inv = client.post(
        f"/workspaces/{wid}/invitations",
        json={"email": "invitee@acme.com", "role": "member"},
    ).json()
    s = client.post(
        "/auth/signup",
        json={
            "email": "invitee@acme.com",
            "password": "password1",
            "invite_token": inv["token"],
        },
    )
    assert s.status_code == 200, s.text
    members = client.get(f"/workspaces/{wid}/members").json()
    assert any(
        m["email"] == "invitee@acme.com" and m["role"] == "member"
        for m in members
    )


def test_signup_invite_email_mismatch_rejected(client) -> None:
    wid = client.get("/me/workspaces").json()[0]["workspace"]["id"]
    inv = client.post(
        f"/workspaces/{wid}/invitations",
        json={"email": "right@acme.com", "role": "member"},
    ).json()
    s = client.post(
        "/auth/signup",
        json={
            "email": "wrong@acme.com",
            "password": "password1",
            "invite_token": inv["token"],
        },
    )
    assert s.status_code == 403
    assert s.json()["detail"]["code"] == "invitation_email_mismatch"


# --- pipeline quota ---------------------------------------------------------


from types import SimpleNamespace


def _quota_settings(per_account: int) -> SimpleNamespace:
    """Minimal stand-in for the fields enforce_pipeline_quota reads, so a test
    can pin a small limit without mutating the frozen global settings."""
    return SimpleNamespace(
        global_pipeline_daily_max=0,
        demo_pipeline_max=3,
        per_account_pipeline_max=per_account,
        per_account_pipeline_window_seconds=3600,
    )


async def _seed_cost_rows(actor: str, n: int) -> None:
    from datetime import datetime, timezone

    from laytimely_api.db.models import AuditEventRow

    async with main_mod._sessionmaker() as session:
        for i in range(n):
            session.add(
                AuditEventRow(
                    actor_sub=actor,
                    action="voyage.create",
                    target_type="voyage",
                    target_id=f"{actor}-{i}",
                    at=datetime.now(timezone.utc),
                    payload_redacted="{}",
                )
            )
        await session.commit()


def test_pipeline_quota_blocks_account_over_limit(monkeypatch) -> None:
    from fastapi import HTTPException

    from laytimely_api.auth import Principal
    from tests.conftest import run_wipe

    monkeypatch.setattr(main_mod, "settings", _quota_settings(5))
    try:
        asyncio.run(_seed_cost_rows("quota-user", 5))
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                main_mod.enforce_pipeline_quota(
                    Principal(id="quota-user", email="q@acme.com")
                )
            )
        assert exc.value.status_code == 429
        assert exc.value.detail["code"] == "account_quota_reached"
    finally:
        run_wipe()


def test_pipeline_quota_allows_under_limit(monkeypatch) -> None:
    from laytimely_api.auth import Principal
    from tests.conftest import run_wipe

    monkeypatch.setattr(main_mod, "settings", _quota_settings(5))
    try:
        asyncio.run(_seed_cost_rows("under-user", 2))
        principal = asyncio.run(
            main_mod.enforce_pipeline_quota(
                Principal(id="under-user", email="u@acme.com")
            )
        )
        assert principal.id == "under-user"
    finally:
        run_wipe()
