"""Add visibility to job_log_lines (public | superadmin)

Revision ID: 005
Revises: 004
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_log_lines",
        sa.Column("visibility", sa.String(20), nullable=False, server_default="public"),
    )


def downgrade() -> None:
    op.drop_column("job_log_lines", "visibility")
