"""Environment-driven settings for the Laytimely API.

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
    # First-party email/password auth (the real multi-user path that does not
    # depend on Cognito). ``app_jwt_secret`` signs the HS256 session token the
    # /auth/signup + /auth/login routes mint and that get_current_user verifies.
    # A dev default keeps localhost working with zero config; production MUST
    # set APP_JWT_SECRET to a long random value (openssl rand -hex 32) so the
    # token cannot be forged. ``app_jwt_ttl_seconds`` is the token lifetime.
    app_jwt_secret: str
    app_jwt_ttl_seconds: int
    # Demo-share accounts. Comma-separated emails (in Doppler) that should get
    # their OWN private copy of the seeded demo cases on signup/login, so a
    # founder can hand out a populated, credentialed demo login. Isolated from
    # the anonymous "Try live demo" identity and from each other.
    demo_share_emails: list[str]
    # Admin dashboard allowlist (cost/usage observability). Comma-separated
    # emails (in Doppler) that may reach the /admin endpoints. Checked
    # server-side against the verified token email on every admin route, so
    # changing who is an admin is a single Doppler edit and nothing in the UI
    # can bypass it. Empty means no one is an admin (fail-closed).
    admin_emails: list[str]
    # Signup gating (cost control). Signup is invite-only: a new account needs a
    # valid matching invitation token. ``signup_bootstrap_code``, when set,
    # additionally lets a founder self-serve a first account without an invite
    # (the bootstrap that mints the first owner who can then invite others).
    # Unset disables the bootstrap path entirely (pure invite-only).
    signup_bootstrap_code: str | None
    # Per-account quota on the expensive (Anthropic-calling) actions: at most
    # ``per_account_pipeline_max`` cost actions per
    # ``per_account_pipeline_window_seconds`` per account, counted from the
    # audit log so it survives restarts and is shared across instances. The
    # shared demo identity gets the tighter ``demo_pipeline_max``. A global
    # daily ceiling (``global_pipeline_daily_max``, 0 disables) bounds total
    # spend across every account as a hard budget kill-switch.
    per_account_pipeline_max: int
    per_account_pipeline_window_seconds: int
    demo_pipeline_max: int
    global_pipeline_daily_max: int
    # Object storage (A3). S3 in production; a local directory otherwise.
    s3_bucket: str | None
    s3_region: str | None
    # Custom S3 endpoint for S3-compatible providers (Cloudflare R2 in the demo).
    # Unset for real AWS S3 — that is the whole storage migration (one var removed).
    s3_endpoint_url: str | None
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
    # Email send via SES (notes/architecture_weeks_5_to_8.md §1.3). Default off
    # so dev environments without an SES identity exercise the sandbox path
    # (audit row + rate limit + 200 response, no outbound). Flip to 1 after
    # the AWS support ticket for production access lands.
    email_send_live: bool
    # Email-in ingestion (notes/architecture_weeks_5_to_8.md §2.3). Shared
    # secret the SES → S3 → Lambda hop signs its forwarded payload with. When
    # unset, the inbound route refuses every call (fail-closed). Generate
    # with ``openssl rand -hex 32`` and put in Doppler / App Runner env.
    email_in_shared_secret: str | None
    # Email-in delivery domain. Per-workspace addresses look like
    # ``<workspace-slug>@<inbox_domain>``; the settings page surfaces this
    # to the workspace admin for use in Gmail / Outlook forwarding rules.
    # Default points at the production tenant; override in dev to keep
    # localhost-rendered tutorials honest.
    inbox_domain: str
    # Multi-tenant workspaces UI flag (notes/architecture_weeks_5_to_8.md
    # §2.1). When off (default), the backend still mints a personal workspace
    # per user (so the data contract is consistent), but the frontend hides
    # the workspace switcher. Flip on per-account when a team needs the UI.
    workspaces_ui: bool
    # Rate limiting for the expensive, paid pipeline trigger (POST /voyages):
    # at most ``rate_limit_max_requests`` per caller per
    # ``rate_limit_window_seconds``. Set the max to 0 to disable. This is a
    # coarse abuse/cost guard, not an auth boundary.
    rate_limit_max_requests: int
    rate_limit_window_seconds: int
    # Audit retention (review #9). Lifespan startup reaps rows older than
    # this many days so the table stays bounded under unbounded growth.
    # 0 disables retention (forever-grow).
    audit_retention_days: int
    # SES sender + invitation accept link base URL (review #12). Used by
    # the workspace invitation email path; the claim-letter SES path keeps
    # using settings.email_send_live + its own helper.
    ses_sender: str | None
    invitation_base_url: str
    # Per-actor rate limit on invitation mint (security hardening). At
    # most ``invitation_rate_limit_max`` per actor per window. Defaults
    # are generous so admins can paste-batch invites.
    invitation_rate_limit_max: int
    invitation_rate_limit_window_seconds: int
    # Interactive API docs (/docs, /redoc, /openapi.json). Off by default so a
    # production deploy does not self-document its (currently open) surface to
    # the world. Set EXPOSE_DOCS=1 for local development.
    expose_docs: bool

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
            app_jwt_secret=(
                os.environ.get("APP_JWT_SECRET")
                or "dev-insecure-app-jwt-secret-change-me"
            ),
            app_jwt_ttl_seconds=int(
                os.environ.get("APP_JWT_TTL_SECONDS") or str(60 * 60 * 24 * 7)
            ),
            admin_emails=[
                e.strip().lower()
                for e in (os.environ.get("ADMIN_EMAILS") or "").split(",")
                if e.strip()
            ],
            demo_share_emails=[
                e.strip().lower()
                for e in (os.environ.get("DEMO_SHARE_EMAILS") or "").split(",")
                if e.strip()
            ],
            signup_bootstrap_code=os.environ.get("SIGNUP_BOOTSTRAP_CODE") or None,
            per_account_pipeline_max=int(
                os.environ.get("PER_ACCOUNT_PIPELINE_MAX") or "5"
            ),
            per_account_pipeline_window_seconds=int(
                os.environ.get("PER_ACCOUNT_PIPELINE_WINDOW_SECONDS") or "3600"
            ),
            demo_pipeline_max=int(os.environ.get("DEMO_PIPELINE_MAX") or "3"),
            global_pipeline_daily_max=int(
                os.environ.get("GLOBAL_PIPELINE_DAILY_MAX") or "0"
            ),
            s3_bucket=os.environ.get("S3_BUCKET") or None,
            s3_region=os.environ.get("S3_REGION") or None,
            s3_endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
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
            email_send_live=(os.environ.get("EMAIL_SEND_LIVE") or "")
            .strip()
            .lower()
            in {"1", "true", "yes", "on"},
            email_in_shared_secret=os.environ.get("EMAIL_IN_SHARED_SECRET") or None,
            inbox_domain=(os.environ.get("INBOX_DOMAIN") or "in.laytimely.com").strip(),
            workspaces_ui=(os.environ.get("WORKSPACES_UI") or "")
            .strip()
            .lower()
            in {"1", "true", "yes", "on"},
            rate_limit_max_requests=int(
                os.environ.get("RATE_LIMIT_MAX_REQUESTS") or "30"
            ),
            rate_limit_window_seconds=int(
                os.environ.get("RATE_LIMIT_WINDOW_SECONDS") or "60"
            ),
            audit_retention_days=int(
                os.environ.get("AUDIT_RETENTION_DAYS") or "90"
            ),
            ses_sender=os.environ.get("SES_SENDER") or None,
            invitation_base_url=(
                os.environ.get("INVITATION_BASE_URL")
                or "http://localhost:3000"
            ).rstrip("/"),
            invitation_rate_limit_max=int(
                os.environ.get("INVITATION_RATE_LIMIT_MAX") or "20"
            ),
            invitation_rate_limit_window_seconds=int(
                os.environ.get("INVITATION_RATE_LIMIT_WINDOW_SECONDS") or "3600"
            ),
            expose_docs=(os.environ.get("EXPOSE_DOCS") or "")
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
