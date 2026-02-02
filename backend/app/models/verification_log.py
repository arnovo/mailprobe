"""VerificationLog model."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)

    mx_hosts: Mapped[list | None] = mapped_column(JSON, nullable=True)
    probe_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # email -> {accepted, detail, ...}
    errors: Mapped[str] = mapped_column(Text, nullable=False, default="")
    best_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    best_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    best_confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
