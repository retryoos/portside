"""voyage_citations (W5/§1.6)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-31 12:00:00.000000

Cache verified analyst citations per (voyage, event). Populated by the
``/voyages/{id}/citations`` route on first read; later reads return the
cached rows so the picker model call only runs once.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voyage_citations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("voyage_id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("citation", sa.Text(), nullable=False),
        sa.Column("tool_used", sa.String(), nullable=False),
        sa.Column("proposition", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["voyage_id"], ["voyages.voyage_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("voyage_citations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_voyage_citations_voyage_id"), ["voyage_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_voyage_citations_event_id"), ["event_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("voyage_citations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_voyage_citations_event_id"))
        batch_op.drop_index(batch_op.f("ix_voyage_citations_voyage_id"))
    op.drop_table("voyage_citations")
