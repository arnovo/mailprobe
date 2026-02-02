"""Celery task: export CSV."""
from __future__ import annotations

import csv
import io

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.tasks.celery_app import celery_app

engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def get_sync_session():
    return SessionLocal()


@celery_app.task(bind=True, max_retries=2)
def run_export_csv(self, workspace_id: int, job_id: str):
    """Generate CSV of leads for workspace, store URL or content in job result."""
    db = get_sync_session()
    try:
        from app.models import Job, Lead
        r = db.execute(select(Job).where(Job.job_id == job_id, Job.workspace_id == workspace_id))
        job = r.scalars().one_or_none()
        if not job:
            return
        job.status = "running"
        job.progress = 20
        db.commit()

        r = db.execute(select(Lead).where(Lead.workspace_id == workspace_id, Lead.opt_out.is_(False)))
        leads = list(r.scalars().all())

        output = io.StringIO()
        writer = csv.writer(output)
        headers = [
            "id", "first_name", "last_name", "title", "company", "domain", "linkedin_url",
            "email_best", "verification_status", "confidence_score", "sales_status",
            "created_at", "updated_at",
        ]
        writer.writerow(headers)
        for lead in leads:
            writer.writerow([
                lead.id, lead.first_name, lead.last_name, lead.title, lead.company, lead.domain,
                lead.linkedin_url, lead.email_best, lead.verification_status, lead.confidence_score,
                lead.sales_status,
                lead.created_at.isoformat() if lead.created_at else "",
                lead.updated_at.isoformat() if lead.updated_at else "",
            ])
        csv_content = output.getvalue()

        job.status = "succeeded"
        job.progress = 100
        job.result = {"csv": csv_content, "row_count": len(leads)}
        db.commit()

        from app.tasks.webhooks import dispatch_webhook_event
        dispatch_webhook_event(workspace_id, "export.completed", {"job_id": job_id, "row_count": len(leads)})
    finally:
        db.close()
