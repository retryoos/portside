"""collapse the viewer role into member

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-01 13:00:00.000000

The role vocabulary drops to owner / admin / member. Any existing membership or
pending invitation at the retired ``viewer`` role is remapped to ``member`` so
no row carries a value the application no longer understands. Roles are stored
as plain strings (no DB enum), so this is a data-only update with no schema
change. Irreversible in a meaningful sense (the original viewer rows can't be
recovered), so downgrade is a no-op.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE memberships SET role = 'member' WHERE role = 'viewer'")
    op.execute("UPDATE invitations SET role = 'member' WHERE role = 'viewer'")


def downgrade() -> None:
    # The viewer role is gone; there is nothing faithful to restore.
    pass
