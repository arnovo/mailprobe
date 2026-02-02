"""Add job log_lines

Revision ID: 002
Revises: 001
Create Date: 2025-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("log_lines", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "log_lines")
