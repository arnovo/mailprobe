"""Celery Beat: retention job - anonymize/delete inactive leads."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.tasks.celery_app import celery_app

engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


@celery_app.task
def run_retention():
    """Anonymize or delete leads not updated in X months (config)."""
    db = SessionLocal()
    try:
        from app.models import Lead

        months = settings.retention_inactive_months
        cutoff = datetime.now(UTC) - timedelta(days=months * 30)
        r = db.execute(select(Lead).where(Lead.updated_at < cutoff))
        leads = list(r.scalars().all())
        for lead in leads:
            lead.first_name = ""
            lead.last_name = ""
            lead.email_best = ""
            lead.email_candidates = None
            lead.linkedin_url = ""
            lead.notes = "[anonymized]"
        db.commit()
    finally:
        db.close()
