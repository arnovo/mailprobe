"""Add smtp_mail_from to workspace_configs (MAIL FROM por workspace)

Revision ID: 007
Revises: 006
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workspace_configs",
        sa.Column("smtp_mail_from", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workspace_configs", "smtp_mail_from")
