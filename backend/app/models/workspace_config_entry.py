"""Per-workspace configuration: key-value (id, workspace_id, key, value). No migrations needed for new keys."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class WorkspaceConfigEntry(Base):
    """A config record: key -> value per workspace. Value is always string (numbers/JSON serialized)."""

    __tablename__ = "workspace_config_entries"
    __table_args__ = (UniqueConstraint("workspace_id", "key", name="uq_workspace_config_workspace_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="config_entries")
