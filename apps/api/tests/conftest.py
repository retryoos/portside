"""Shared pytest fixtures.

The suite runs against an isolated, throwaway SQLite database, never the
configured ``DATABASE_URL`` (which in local dev points at the live Neon
instance). We force a temp SQLite URL *before* importing the app, so the
module-level engine binds to it, and migrate the schema once so the
workspace-state wipe below has tables to truncate. This keeps tests from ever
connecting to, or truncating tables in, the real database.

Workspace-touching route tests share that one SQLite file (the
``_sessionmaker`` lives at module scope), so state from one test file bleeds
into the next unless we truncate the workspace-related tables between runs.
Lifting the wipe helper into conftest stops every test file from re-defining
it (review followup).
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

# Force an isolated SQLite test DB before importing the app. ``settings`` reads
# DATABASE_URL at import time, and its .env loader uses ``setdefault`` (existing
# env wins), so setting it here pins the engine to a throwaway file and the
# real (Neon) database is never touched by the suite.
_TEST_DB_PATH = Path(tempfile.gettempdir()) / "portside_pytest.db"
_TEST_DB_PATH.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"
# Signup is invite-only; give the suite a bootstrap code so route-level signup
# tests can create an account without first minting an invite.
os.environ.setdefault("SIGNUP_BOOTSTRAP_CODE", "test-bootstrap")
# Disable the per-account / demo pipeline quotas for the suite at large (the
# shared dev/demo identity would otherwise trip them across the many upload
# tests). The quota's own tests re-enable a small limit via monkeypatch.
os.environ.setdefault("PER_ACCOUNT_PIPELINE_MAX", "100000")
os.environ.setdefault("DEMO_PIPELINE_MAX", "100000")
# The dev-auth principal's email, so admin-route tests run as an admin.
os.environ.setdefault("ADMIN_EMAILS", "demo@laytimely.com")

# pylint: disable=wrong-import-position
from laytimely_api import main as main_mod  # noqa: E402
from laytimely_api.db.engine import run_migrations  # noqa: E402
from laytimely_api.db.models import (  # noqa: E402
    AuditEventRow,
    InvitationRow,
    MembershipRow,
    WorkspaceRow,
)
from sqlalchemy import delete  # noqa: E402

# Build the schema once up front so ``run_wipe()`` has tables to truncate even
# when it runs before a TestClient lifespan has migrated. The app's own startup
# migration is then a no-op (already at head).
run_migrations(os.environ["DATABASE_URL"])


async def wipe_workspace_state() -> None:
    """Truncate every workspace-related table so route tests do not
    inherit memberships, invitations, or audit rows from a prior file.
    Importable from any test file that needs it explicitly; pytest will
    not auto-run it because it is not a fixture.
    """
    async with main_mod._sessionmaker() as session:
        async with session.begin():
            await session.execute(delete(InvitationRow))
            await session.execute(delete(MembershipRow))
            await session.execute(delete(WorkspaceRow))
            await session.execute(delete(AuditEventRow))


def run_wipe() -> None:
    """Synchronous wrapper for use inside a sync pytest fixture body."""
    asyncio.run(wipe_workspace_state())
