"""Environment-driven settings for the Papership.Ai API.

Cross-cutting config used by the FastAPI app + the agent fleet. Values come from
environment variables; a ``.env`` file at the repo root or ``apps/api/.env`` is
loaded once at import time for local-dev convenience (no python-dotenv
dependency — we just parse it ourselves; production deploys pass real env vars).

Reading these via ``os.environ.get(...)`` elsewhere stays valid — ``Settings``
just centralises defaults + CORS list parsing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_DEFAULT_MODEL_PRIMARY = "claude-sonnet-4-6"
_DEFAULT_MODEL_ESCAPE = "claude-opus-4-7"
_DEFAULT_REQUEST_TIMEOUT_S = "30"
_DEFAULT_CORS_ORIGINS = "http://localhost:3000"
# Local-dev default: a SQLite file next to the package. Production sets
# DATABASE_URL to the Aurora Postgres URL (postgresql+asyncpg://...).
_DEFAULT_DATABASE_URL = (
    f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent / 'portside.db'}"
)
# Local-dev object storage: a directory next to the package. Production sets
# S3_BUCKET (uploaded PDFs go to S3 instead).
_DEFAULT_OBJECTS_DIR = str(Path(__file__).resolve().parent.parent / "_objects")

_LOADED = False


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    model_primary: str
    model_escape: str
    request_timeout_s: float
    cors_origins: list[str]
    database_url: str
    # Auth (A2). dev_auth bypasses JWT verification and returns a fixed dev user
    # — the non-blocking path until Cognito is provisioned. The Cognito fields
    # drive real verification once dev_auth is off.
    dev_auth: bool
    cognito_region: str | None
    cognito_user_pool_id: str | None
    cognito_client_id: str | None
    # Object storage (A3). S3 in production; a local directory otherwise.
    s3_bucket: str | None
    s3_region: str | None
    s3_prefix: str
    objects_dir: str
    # A4: a voyage left in a non-terminal pipeline stage with no progress for
    # this many seconds is treated as an interrupted run (its driving task died
    # with a previous instance) and reaped to "error" on startup.
    stale_run_seconds: int
    # A7: when off, the research tools serve a committed offline fixture; when
    # on, they may attempt a live API (seam for a real weather/calendar feed).
    research_live: bool
    # Legal citation subsystem (notes/architecture_weeks_5_to_8.md §1.6). When
    # off (default), corpus + IMO conventions are the only sources. Flipping
    # `legal_eur_lex_live=1` enables the CELLAR client; flipping
    # `legal_bailii_live=1` enables a polite BAILII scraper (phase 2).
    legal_eur_lex_live: bool
    legal_bailii_live: bool

    @classmethod
    def load(cls) -> "Settings":
        _load_dotenv_files_once()
        cors_raw = os.environ.get("CORS_ORIGINS") or _DEFAULT_CORS_ORIGINS
        timeout_raw = os.environ.get("REQUEST_TIMEOUT_S") or _DEFAULT_REQUEST_TIMEOUT_S
        pool_id = os.environ.get("COGNITO_USER_POOL_ID") or None
        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
            model_primary=os.environ.get(
                "ANTHROPIC_MODEL_PRIMARY", _DEFAULT_MODEL_PRIMARY
            ),
            model_escape=os.environ.get(
                "ANTHROPIC_MODEL_ESCAPE", _DEFAULT_MODEL_ESCAPE
            ),
            request_timeout_s=float(timeout_raw),
            cors_origins=_parse_cors_origins(cors_raw),
            database_url=os.environ.get("DATABASE_URL") or _DEFAULT_DATABASE_URL,
            dev_auth=_parse_dev_auth(os.environ.get("DEV_AUTH"), pool_id),
            cognito_region=os.environ.get("COGNITO_REGION") or None,
            cognito_user_pool_id=pool_id,
            cognito_client_id=os.environ.get("COGNITO_CLIENT_ID") or None,
            s3_bucket=os.environ.get("S3_BUCKET") or None,
            s3_region=os.environ.get("S3_REGION") or None,
            s3_prefix=os.environ.get("S3_PREFIX") or "",
            objects_dir=os.environ.get("OBJECTS_DIR") or _DEFAULT_OBJECTS_DIR,
            stale_run_seconds=int(os.environ.get("STALE_RUN_SECONDS") or "900"),
            research_live=(os.environ.get("RESEARCH_LIVE") or "").strip().lower()
            in {"1", "true", "yes", "on"},
            legal_eur_lex_live=(os.environ.get("LEGAL_EUR_LEX_LIVE") or "")
            .strip()
            .lower()
            in {"1", "true", "yes", "on"},
            legal_bailii_live=(os.environ.get("LEGAL_BAILII_LIVE") or "")
            .strip()
            .lower()
            in {"1", "true", "yes", "on"},
        )

    @property
    def cognito_issuer(self) -> str | None:
        if not (self.cognito_region and self.cognito_user_pool_id):
            return None
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )

    @property
    def cognito_jwks_url(self) -> str | None:
        issuer = self.cognito_issuer
        return f"{issuer}/.well-known/jwks.json" if issuer else None


def _parse_dev_auth(raw: str | None, pool_id: str | None) -> bool:
    """DEV_AUTH explicit wins; otherwise default to dev auth when no Cognito
    pool is configured (so local dev works with no token, prod with a pool
    enforces real auth unless explicitly overridden)."""
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return pool_id is None


def _parse_cors_origins(raw: str) -> list[str]:
    """Comma-separated list, stripped, no empties."""
    return [item.strip() for item in raw.split(",") if item.strip()]


def _find_repo_root(start: Path | None = None) -> Path | None:
    """Walk up from ``start`` (default: this file) looking for a ``.git`` dir."""
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _parse_dotenv(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict. Blank lines + ``#`` comments are skipped.

    No quoting magic — a line like ``KEY=VALUE`` produces ``{"KEY": "VALUE"}``.
    Returns an empty dict if the file is missing or unreadable.
    """
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        out[key.strip()] = value.strip()
    return out


def _load_dotenv_files_once() -> None:
    """Best-effort load of repo-root ``.env`` then ``apps/api/.env``. Idempotent.

    Lines of the form ``KEY=VALUE``; existing env vars win (so real prod env
    beats file). Ignores blank lines and lines starting with ``#``. No quoting
    magic — keep it boring.
    """
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    root = _find_repo_root()
    if root is None:
        return
    for candidate in (root / ".env", root / "apps" / "api" / ".env"):
        for key, value in _parse_dotenv(candidate).items():
            os.environ.setdefault(key, value)


settings = Settings.load()
