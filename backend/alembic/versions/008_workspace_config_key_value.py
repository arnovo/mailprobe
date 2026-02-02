"""Reemplazar workspace_configs por tabla clave-valor (workspace_config_entries).

Revision ID: 008
Revises: 007
Create Date: 2026-02-02

Estructura: id, workspace_id, key, value. Para añadir nueva config solo se inserta un registro.
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspace_config_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "key", name="uq_workspace_config_workspace_key"),
    )
    op.create_index("ix_workspace_config_entries_workspace_id", "workspace_config_entries", ["workspace_id"], unique=False)

    # Migrar datos desde workspace_configs
    conn = op.get_bind()
    rp = conn.execute(sa.text("SELECT workspace_id, smtp_timeout_seconds, dns_timeout_seconds, enabled_pattern_indices, smtp_mail_from FROM workspace_configs"))
    rows = rp.fetchall()
    for row in rows:
        workspace_id, smtp, dns, indices, mail_from = row
        if smtp is not None:
            conn.execute(
                sa.text("INSERT INTO workspace_config_entries (workspace_id, key, value) VALUES (:wid, 'smtp_timeout_seconds', :v)"),
                {"wid": workspace_id, "v": str(smtp)},
            )
        if dns is not None:
            conn.execute(
                sa.text("INSERT INTO workspace_config_entries (workspace_id, key, value) VALUES (:wid, 'dns_timeout_seconds', :v)"),
                {"wid": workspace_id, "v": str(dns)},
            )
        if indices is not None and len(indices) >= 5:
            conn.execute(
                sa.text("INSERT INTO workspace_config_entries (workspace_id, key, value) VALUES (:wid, 'enabled_pattern_indices', :v)"),
                {"wid": workspace_id, "v": json.dumps(indices)},
            )
        if mail_from is not None and (mail_from or "").strip():
            conn.execute(
                sa.text("INSERT INTO workspace_config_entries (workspace_id, key, value) VALUES (:wid, 'smtp_mail_from', :v)"),
                {"wid": workspace_id, "v": mail_from.strip()},
            )

    op.drop_table("workspace_configs")


def downgrade() -> None:
    op.create_table(
        "workspace_configs",
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("smtp_timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("dns_timeout_seconds", sa.Float(), nullable=True),
        sa.Column("enabled_pattern_indices", sa.JSON(), nullable=True),
        sa.Column("smtp_mail_from", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("workspace_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )
    conn = op.get_bind()
    rp = conn.execute(sa.text("SELECT workspace_id, key, value FROM workspace_config_entries"))
    rows = rp.fetchall()
    workspaces_seen = set()
    for workspace_id, key, value in rows:
        if workspace_id not in workspaces_seen:
            conn.execute(sa.text(
                "INSERT INTO workspace_configs (workspace_id, smtp_timeout_seconds, dns_timeout_seconds, enabled_pattern_indices, smtp_mail_from) VALUES (:wid, NULL, NULL, NULL, NULL)"
            ), {"wid": workspace_id})
            workspaces_seen.add(workspace_id)
    for workspace_id, key, value in rows:
        if key == "smtp_timeout_seconds":
            conn.execute(sa.text("UPDATE workspace_configs SET smtp_timeout_seconds = :v WHERE workspace_id = :wid"), {"v": int(value), "wid": workspace_id})
        elif key == "dns_timeout_seconds":
            conn.execute(sa.text("UPDATE workspace_configs SET dns_timeout_seconds = :v WHERE workspace_id = :wid"), {"v": float(value), "wid": workspace_id})
        elif key == "enabled_pattern_indices":
            conn.execute(sa.text("UPDATE workspace_configs SET enabled_pattern_indices = :v WHERE workspace_id = :wid"), {"v": json.dumps(json.loads(value)), "wid": workspace_id})
        elif key == "smtp_mail_from":
            conn.execute(sa.text("UPDATE workspace_configs SET smtp_mail_from = :v WHERE workspace_id = :wid"), {"v": value, "wid": workspace_id})
    op.drop_index("ix_workspace_config_entries_workspace_id", table_name="workspace_config_entries")
    op.drop_table("workspace_config_entries")
