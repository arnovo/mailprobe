"""Change lead verification_status default to pending.

Revision ID: 010
Revises: 009
Create Date: 2026-02-02
"""
from alembic import op
import sqlalchemy as sa


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cambiar default de verification_status de 'unknown' a 'pending'
    op.alter_column(
        "leads",
        "verification_status",
        server_default="pending",
    )
    # Actualizar leads sin verificar (sin email_best) a 'pending'
    op.execute("""
        UPDATE leads 
        SET verification_status = 'pending' 
        WHERE (email_best = '' OR email_best IS NULL) 
          AND verification_status = 'unknown'
    """)


def downgrade() -> None:
    op.alter_column(
        "leads",
        "verification_status",
        server_default="unknown",
    )
    op.execute("""
        UPDATE leads 
        SET verification_status = 'unknown' 
        WHERE verification_status = 'pending'
    """)
