"""Job model for async tasks."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )  # para jobs kind=verify
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # uuid
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # verify, export_csv, import_csv, webhook_delivery
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")  # queued|running|succeeded|failed
    progress: Mapped[int] = mapped_column(default=0, nullable=False)  # 0-100
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    log_lines: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["Verifying domain...", ...]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
