"""First-party email/password accounts (real multi-user auth).

This is the identity layer that turns the formerly single-stub-user app into a
real multi-tenant product: people sign up, log in, and accept invitations as
distinct principals. It deliberately does NOT depend on Cognito so the product
works end to end today; the Cognito path in ``auth.py`` stays available for a
later managed-pool migration (both verify into the same ``Principal``).

Design choices:

* Passwords are hashed with PBKDF2-HMAC-SHA256 from the standard library
  (600k iterations, 16-byte per-user salt). No native dependency, FIPS-approved
  primitive, constant-time verification. The stored format is self-describing
  (``pbkdf2_sha256$iterations$salt_hex$hash_hex``) so the work factor can be
  raised later without a migration.
* The session token is a short HS256 JWT signed with ``settings.app_jwt_secret``
  carrying ``sub`` / ``email`` / ``name``. ``auth.get_current_user`` verifies it.
* ``email_lower`` is the unique key; ``email`` keeps the user's original casing.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db.models import User
from .settings import settings

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_PBKDF2_ITERATIONS = 600_000
_PBKDF2_ALGO = "pbkdf2_sha256"

_MIN_PASSWORD = 8
_MAX_PASSWORD = 200  # bcrypt-style sanity cap; also bounds PBKDF2 work.


# ---------------------------------------------------------------------------
# Password hashing (stdlib PBKDF2)
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a self-describing PBKDF2 hash string for ``password``."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"{_PBKDF2_ALGO}${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    """Constant-time check of ``password`` against a stored hash.

    Returns False for any malformed/empty stored value rather than raising, so
    a row with no password (legacy seed/dev users) simply can't be logged into.
    """
    if not stored:
        return False
    try:
        algo, iters_s, salt_hex, hash_hex = stored.split("$", 3)
    except ValueError:
        return False
    if algo != _PBKDF2_ALGO:
        return False
    try:
        iterations = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)


# ---------------------------------------------------------------------------
# Session token (HS256 JWT)
# ---------------------------------------------------------------------------


def issue_app_token(*, sub: str, email: str | None, name: str | None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "name": name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.app_jwt_ttl_seconds)).timestamp()),
        "iss": "laytimely",
    }
    return jwt.encode(payload, settings.app_jwt_secret, algorithm="HS256")


def verify_app_token(token: str) -> dict:
    """Decode + verify an app session token. Raises ``jwt.PyJWTError`` on any
    failure (expired, bad signature, wrong issuer)."""
    return jwt.decode(
        token,
        settings.app_jwt_secret,
        algorithms=["HS256"],
        issuer="laytimely",
        options={"require": ["exp", "sub"]},
    )


# ---------------------------------------------------------------------------
# Wire models
# ---------------------------------------------------------------------------


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=_MIN_PASSWORD, max_length=_MAX_PASSWORD)
    name: str | None = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value: str) -> str:
        v = value.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _strip_email(cls, value: str) -> str:
        return value.strip()


class AuthUser(BaseModel):
    sub: str
    email: str | None
    name: str | None


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class AccountError(RuntimeError):
    """Stable-code error so the route maps to a precise HTTP status without
    string-sniffing. ``email_taken`` -> 409, ``invalid_credentials`` -> 401."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def _display_name(name: str | None, email: str) -> str:
    if name and name.strip():
        return name.strip()
    return email.split("@", 1)[0]


async def create_account(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    name: str | None = None,
) -> User:
    """Create a new account. Raises ``AccountError('email_taken')`` if the
    case-folded email already exists. Caller commits."""
    email = email.strip()
    email_lower = email.lower()
    existing = (
        await session.execute(
            select(User).where(User.email_lower == email_lower)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AccountError("email_taken", "an account with this email already exists")
    user = User(
        id=uuid.uuid4().hex,
        email=email,
        email_lower=email_lower,
        password_hash=hash_password(password),
        name=_display_name(name, email),
    )
    session.add(user)
    await session.flush()
    return user


async def authenticate(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User:
    """Return the user on valid credentials, else raise
    ``AccountError('invalid_credentials')``. The same error (and a dummy hash
    verification on the no-user path) keeps the timing/shape uniform so we do
    not leak whether an email is registered."""
    email_lower = email.strip().lower()
    user = (
        await session.execute(
            select(User).where(User.email_lower == email_lower)
        )
    ).scalar_one_or_none()
    if user is None:
        # Burn a comparable amount of time so "no such user" and "wrong
        # password" are indistinguishable to a timing attacker.
        verify_password(password, hash_password("dummy"))
        raise AccountError("invalid_credentials", "invalid email or password")
    if not verify_password(password, user.password_hash):
        raise AccountError("invalid_credentials", "invalid email or password")
    return user


def to_auth_user(user: User) -> AuthUser:
    return AuthUser(sub=user.id, email=user.email, name=user.name)
