"""Lead model."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    first_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    company: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    domain: Mapped[str] = mapped_column(String(255), nullable=False, default="", index=True)
    linkedin_url: Mapped[str] = mapped_column(String(512), nullable=False, default="", index=True)

    email_best: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email_candidates: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # list of strings
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending|valid|risky|unknown|invalid
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mx_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    catch_all: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    smtp_check: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    web_mentioned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # email citado en fuentes públicas
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)  # array of strings

    sales_status: Mapped[str] = mapped_column(String(50), nullable=False, default="New")  # New|Contacted|Replied|Interested|NotNow|Unsubscribed

    # Compliance
    source: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    lawful_basis: Mapped[str] = mapped_column(String(100), nullable=False, default="legitimate_interest")
    purpose: Mapped[str] = mapped_column(String(255), nullable=False, default="b2b_sales_outreach")
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="leads")
