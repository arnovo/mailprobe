"""Add job lead_id for verification-log lookup

Revision ID: 003
Revises: 002
Create Date: 2025-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_jobs_lead_id", "jobs", "leads", ["lead_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_jobs_lead_id", "jobs", ["lead_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_jobs_lead_id", table_name="jobs")
    op.drop_constraint("fk_jobs_lead_id", "jobs", type_="foreignkey")
    op.drop_column("jobs", "lead_id")
