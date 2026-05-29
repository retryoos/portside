"""Auth (A2): resolve the current user from a Cognito JWT.

``dev_auth`` bypasses verification and returns a fixed dev user — the
non-blocking path used in tests and locally until Panos provisions the Cognito
pool (notes/19). When ``dev_auth`` is off, the bearer token is verified against
the pool's JWKS (RS256, issuer + audience); going live is then purely a config
swap (set COGNITO_* and DEV_AUTH=0), no code change.
"""

from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient
from pydantic import BaseModel

from .settings import settings

# Owner id for dev-auth requests and for the seeded demo voyages, so the dev
# user actually sees the seeds once owner-scoping is on.
DEV_USER_ID = "dev-user"
DEV_USER_EMAIL = "dev@portside.local"


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
        raise HTTPException(
            status_code=401, detail=f"invalid token: {exc}"
        ) from exc


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> Principal:
    """FastAPI dependency: the authenticated principal for the request."""
    if settings.dev_auth:
        return Principal(id=DEV_USER_ID, email=DEV_USER_EMAIL)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    claims = _verify_cognito_jwt(token)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="token missing sub")
    return Principal(id=sub, email=claims.get("email"))
