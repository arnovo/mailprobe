"""Líneas de log de un job (almacenadas en tabla para consulta y auditoría)."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobLogLine(Base):
    __tablename__ = "job_log_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(Text, nullable=False, default="info")  # info | debug | error
    # public = visible para cualquier usuario del workspace; superadmin = solo superadmin (logs más detallados/comprometedores)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
