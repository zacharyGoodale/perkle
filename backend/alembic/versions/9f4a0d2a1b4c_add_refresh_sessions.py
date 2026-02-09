"""add refresh sessions

Revision ID: 9f4a0d2a1b4c
Revises: f3495c7f2d0f
Create Date: 2026-02-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f4a0d2a1b4c"
down_revision: Union[str, Sequence[str], None] = "f3495c7f2d0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("jti_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.String(length=26), nullable=True),
        sa.Column("expires_at", sa.String(length=26), nullable=False),
        sa.Column("revoked_at", sa.String(length=26), nullable=True),
        sa.Column("last_used_at", sa.String(length=26), nullable=True),
        sa.Column("rotated_from_id", sa.String(length=36), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(["rotated_from_id"], ["refresh_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("refresh_sessions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_refresh_sessions_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_refresh_sessions_jti_hash"), ["jti_hash"], unique=True)
        batch_op.create_index("ix_refresh_sessions_user_active", ["user_id", "revoked_at"], unique=False)
        batch_op.create_index("ix_refresh_sessions_expires_at", ["expires_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("refresh_sessions", schema=None) as batch_op:
        batch_op.drop_index("ix_refresh_sessions_expires_at")
        batch_op.drop_index("ix_refresh_sessions_user_active")
        batch_op.drop_index(batch_op.f("ix_refresh_sessions_jti_hash"))
        batch_op.drop_index(batch_op.f("ix_refresh_sessions_user_id"))

    op.drop_table("refresh_sessions")
