"""Create workspace_configs table (timeouts and candidate patterns per workspace)

Revision ID: 006
Revises: 005
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspace_configs",
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("smtp_timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("dns_timeout_seconds", sa.Float(), nullable=True),
        sa.Column("enabled_pattern_indices", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("workspace_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("workspace_configs")
