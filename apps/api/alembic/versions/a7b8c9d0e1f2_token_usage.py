"""token_usage table (admin observability)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-01 20:00:00.000000

Per-call Anthropic token usage, captured at the LLM chokepoint so the admin
dashboard can aggregate spend by user, feature, model, and API key fingerprint.
Append-only; bounded later by the same retention reaper as the audit log.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "token_usage",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_sub", sa.String(), nullable=True),
        sa.Column("voyage_id", sa.String(), nullable=True),
        sa.Column("feature", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=False),
        sa.Column("key_fp", sa.String(), nullable=True),
        sa.Column("key_label", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_usage_at", "token_usage", ["at"])
    op.create_index("ix_token_usage_actor_sub", "token_usage", ["actor_sub"])
    op.create_index("ix_token_usage_voyage_id", "token_usage", ["voyage_id"])
    op.create_index("ix_token_usage_feature", "token_usage", ["feature"])
    op.create_index("ix_token_usage_model", "token_usage", ["model"])
    op.create_index("ix_token_usage_key_fp", "token_usage", ["key_fp"])


def downgrade() -> None:
    op.drop_index("ix_token_usage_key_fp", table_name="token_usage")
    op.drop_index("ix_token_usage_model", table_name="token_usage")
    op.drop_index("ix_token_usage_feature", table_name="token_usage")
    op.drop_index("ix_token_usage_voyage_id", table_name="token_usage")
    op.drop_index("ix_token_usage_actor_sub", table_name="token_usage")
    op.drop_index("ix_token_usage_at", table_name="token_usage")
    op.drop_table("token_usage")
