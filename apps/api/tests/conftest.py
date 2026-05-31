"""Shared pytest fixtures.

Workspace-touching route tests share the same SQLite file (the
``_sessionmaker`` lives at module scope), so state from one test file
bleeds into the next unless we truncate the workspace-related tables
between runs. Lifting the wipe helper into conftest stops every test
file from re-defining it (review followup).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# pylint: disable=wrong-import-position
from portside_api import main as main_mod  # noqa: E402
from portside_api.db.models import (  # noqa: E402
    AuditEventRow,
    InvitationRow,
    MembershipRow,
    WorkspaceRow,
)
from sqlalchemy import delete  # noqa: E402


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
