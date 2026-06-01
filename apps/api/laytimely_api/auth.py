"""Auth (A2): resolve the current user from the request's bearer token.

Three verification paths, tried in order (see ``get_current_user``):

1. ``dev_auth`` on returns a fixed dev user, the non-blocking path used in
   tests and zero-config local dev.
2. A first-party app session token (HS256, minted by /auth/login and
   /auth/signup). This is the real multi-user identity layer.
3. A Cognito IdToken verified against the pool JWKS (RS256), available when a
   pool is configured so a managed-pool migration needs no call-site changes.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient
from pydantic import BaseModel

from .settings import settings

logger = logging.getLogger("laytimely_api.auth")

# Owner id for dev-auth requests and for the seeded demo voyages, so the dev
# user actually sees the seeds once owner-scoping is on.
DEV_USER_ID = "dev-user"
DEV_USER_EMAIL = "demo@laytimely.com"


class Principal(BaseModel):
    id: str
    email: str | None = None


@lru_cache(maxsize=4)
def _jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _verify_cognito_jwt(token: str) -> dict:
    jwks_url = settings.cognito_jwks_url
    issuer = settings.cognito_issuer
    if not (jwks_url and issuer and settings.cognito_client_id):
        raise HTTPException(status_code=500, detail="auth is not configured")
    try:
        signing_key = _jwk_client(jwks_url).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.cognito_client_id,
            issuer=issuer,
        )
    except jwt.PyJWTError as exc:
        # Don't echo PyJWT's internals back to the caller; a generic 401 is
        # enough for the client and avoids leaking verifier details.
        logger.warning("rejected token: %s", exc)
        raise HTTPException(status_code=401, detail="invalid token") from exc


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> Principal:
    """FastAPI dependency: the authenticated principal for the request."""
    if settings.dev_auth:
        return Principal(id=DEV_USER_ID, email=DEV_USER_EMAIL)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()

    # 1) First-party app session token. Imported lazily to avoid an import
    # cycle (accounts -> settings; auth is imported very early in app boot).
    from . import accounts

    try:
        claims = accounts.verify_app_token(token)
    except jwt.PyJWTError:
        claims = None
    if claims is not None:
        sub = claims.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="token missing sub")
        return Principal(id=sub, email=claims.get("email"))

    # 2) Cognito IdToken, only if a pool is configured. Otherwise the app
    # token was the only valid option and it failed, so reject.
    if not settings.cognito_issuer:
        raise HTTPException(status_code=401, detail="invalid token")
    claims = _verify_cognito_jwt(token)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="token missing sub")
    return Principal(id=sub, email=claims.get("email"))
