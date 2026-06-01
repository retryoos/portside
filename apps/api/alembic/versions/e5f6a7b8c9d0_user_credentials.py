"""users credential columns (real multi-user auth)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-01 12:00:00.000000

Adds the columns that turn the formerly-ownership-only ``users`` table into a
real account store: ``email_lower`` (case-folded unique login key + index),
``password_hash`` (argon2), and ``name`` (display). All nullable so existing
seed/dev rows keep validating; only accounts minted via /auth/signup carry a
password. The unique index on ``email_lower`` is what prevents two accounts
sharing one email.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email_lower", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("password_hash", sa.String(), nullable=True)
        )
        batch_op.add_column(sa.Column("name", sa.String(), nullable=True))
        batch_op.create_index(
            "ix_users_email_lower", ["email_lower"], unique=True
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_email_lower")
        batch_op.drop_column("name")
        batch_op.drop_column("password_hash")
        batch_op.drop_column("email_lower")
