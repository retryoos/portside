"""audit_events

Revision ID: a1b2c3d4e5f6
Revises: f555fafd0771
Create Date: 2026-05-31 00:00:00.000000

W7/§2.2 audit log. New append-only table; no existing rows to migrate.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f555fafd0771"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_sub", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column(
            "at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "payload_redacted",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_events_actor_sub"), "audit_events", ["actor_sub"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_action"), "audit_events", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_target_type"),
        "audit_events",
        ["target_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_target_id"),
        "audit_events",
        ["target_id"],
        unique=False,
    )
    op.create_index(op.f("ix_audit_events_at"), "audit_events", ["at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_at"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_target_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_target_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_action"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_actor_sub"), table_name="audit_events")
    op.drop_table("audit_events")
