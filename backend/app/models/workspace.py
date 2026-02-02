"""Workspace and WorkspaceUser models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.lead import Lead
    from app.models.user import User
    from app.models.webhook import Webhook
    from app.models.workspace_config_entry import WorkspaceConfigEntry


class WorkspaceRole:
    ADMIN = "admin"
    MEMBER = "member"
    READ_ONLY = "read_only"


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")  # free, pro, team
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    workspace_users: Mapped[list[WorkspaceUser]] = relationship("WorkspaceUser", back_populates="workspace")
    leads: Mapped[list[Lead]] = relationship("Lead", back_populates="workspace")
    api_keys: Mapped[list[ApiKey]] = relationship("ApiKey", back_populates="workspace")
    webhooks: Mapped[list[Webhook]] = relationship("Webhook", back_populates="workspace")
    config_entries: Mapped[list[WorkspaceConfigEntry]] = relationship(
        "WorkspaceConfigEntry", back_populates="workspace", uselist=True, cascade="all, delete-orphan"
    )


class WorkspaceUser(Base):
    __tablename__ = "workspace_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=WorkspaceRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="workspace_users")
    user: Mapped[User] = relationship("User", back_populates="workspace_users")
