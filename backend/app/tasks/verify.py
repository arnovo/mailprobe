"""Celery task: verify lead (find candidates + verify + update lead)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Sync engine for Celery (worker runs outside async)
from app.core.config import settings as s
from app.core.log_constants import LogCode, LogParam
from app.core.log_service import VerificationLogger, make_log_message
from app.services.verifier import verify_and_pick_best
from app.services.workspace_config import get_workspace_config_sync
from app.tasks.celery_app import celery_app

if TYPE_CHECKING:
    from app.models import Job

engine = create_engine(s.database_url_sync, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)

# Verification can take a while (DNS, multiple MX, SMTP per candidate). Task limit: 10 min soft, 11 min hard.
VERIFY_SOFT_TIME_LIMIT = 600
VERIFY_TIME_LIMIT = 660
MAX_LOGGED_CANDIDATES = 15


def get_sync_session() -> Session:
    return SessionLocal()


def _log_level_from_code(code: LogCode | str) -> str:
    """Determine log level from code."""
    code_str = code if isinstance(code, str) else code.value
    if code_str.startswith("DEBUG_"):
        return "debug"
    if code_str.startswith("ERROR_") or code_str in ("JOB_FAILED", "JOB_TIMEOUT"):
        return "error"
    return "info"


def _visibility_from_code(code: LogCode | str) -> str:
    """Determine visibility from code."""
    code_str = code if isinstance(code, str) else code.value
    if code_str.startswith("DEBUG_"):
        return "superadmin"
    return "public"


def _append_log(
    db: Session,
    job: Job,
    code: LogCode | str,
    params: dict | None = None,
    level: str | None = None,
    visibility: str | None = None,
) -> None:
    """Append a log line with i18n code to job_log_lines table."""
    from app.models import JobLogLine

    message = make_log_message(code, params)
    job.log_lines = (job.log_lines or []) + [message]
    seq = len(job.log_lines) - 1
    lvl = level or _log_level_from_code(code)
    vis = visibility or _visibility_from_code(code)
    db.add(JobLogLine(job_id=job.id, seq=seq, message=message, level=lvl, visibility=vis))


def _mark_job_failed(db: Session, job_id: str, workspace_id: int, reason: str, code: LogCode | None = None) -> None:
    """Update job to failed and commit."""
    from app.models import Job

    r = db.execute(select(Job).where(Job.job_id == job_id, Job.workspace_id == workspace_id))
    job = r.scalars().one_or_none()
    if job:
        _append_log(db, job, code or LogCode.JOB_FAILED, {LogParam.REASON: reason}, level="error", visibility="public")
        job.status = "failed"
        job.error = reason[:500]
        db.commit()


def _create_job_logger(db: Session, job: Job) -> VerificationLogger:
    """Create a VerificationLogger that saves to the job's log_lines."""

    def detail_callback(message: str) -> None:
        """Save detail messages to job log."""
        from app.models import JobLogLine

        job.log_lines = (job.log_lines or []) + [message]
        seq = len(job.log_lines) - 1
        # Parse message to determine level/visibility
        from app.core.log_service import parse_log_message

        code, _ = parse_log_message(message)
        level = _log_level_from_code(code) if code else "debug"
        visibility = _visibility_from_code(code) if code else "superadmin"
        db.add(JobLogLine(job_id=job.id, seq=seq, message=message, level=level, visibility=visibility))
        db.commit()

    def progress_callback(message: str | None, email: str | None, smtp_response: str | None) -> None:
        """Save progress messages to job log."""
        from app.models import JobLogLine

        if message:
            job.log_lines = (job.log_lines or []) + [message]
            seq = len(job.log_lines) - 1
            # Parse message to determine level/visibility
            from app.core.log_service import parse_log_message

            code, _ = parse_log_message(message)
            level = _log_level_from_code(code) if code else "info"
            visibility = _visibility_from_code(code) if code else "public"
            db.add(JobLogLine(job_id=job.id, seq=seq, message=message, level=level, visibility=visibility))
            db.commit()

    return VerificationLogger(detail_callback=detail_callback, progress_callback=progress_callback)


@celery_app.task(bind=True, max_retries=3, soft_time_limit=VERIFY_SOFT_TIME_LIMIT, time_limit=VERIFY_TIME_LIMIT)
def run_verify_lead(self, lead_id: int, workspace_id: int, job_id: str):
    """Verify lead: generate candidates, verify best, update lead and job."""
    db = get_sync_session()
    try:
        from app.models import Job, Lead, Usage, VerificationLog

        r = db.execute(select(Job).where(Job.job_id == job_id, Job.workspace_id == workspace_id))
        job = r.scalars().one_or_none()
        if not job:
            return
        if job.status == "cancelled":
            return
        job.status = "running"
        job.progress = 10
        job.log_lines = job.log_lines or []
        _append_log(
            db,
            job,
            LogCode.JOB_STARTED,
            {LogParam.JOB_TYPE: "verify", LogParam.LEAD_ID: lead_id, LogParam.WORKSPACE_ID: workspace_id},
            visibility="public",
        )
        _append_log(db, job, LogCode.JOB_STARTING_VERIFICATION, visibility="public")
        _append_log(
            db,
            job,
            LogCode.DEBUG_WORKER_PROCESSING,
            {LogParam.JOB_ID: job_id, LogParam.LEAD_ID: lead_id, LogParam.WORKSPACE_ID: workspace_id},
            visibility="superadmin",
        )
        db.commit()

        r = db.execute(select(Lead).where(Lead.id == lead_id, Lead.workspace_id == workspace_id))
        lead = r.scalars().one_or_none()
        if not lead:
            _append_log(
                db, job, LogCode.ERROR_LEAD_NOT_FOUND, {LogParam.LEAD_ID: lead_id}, level="error", visibility="public"
            )
            job.status = "failed"
            job.error = "Lead not found"
            db.commit()
            return
        if lead.opt_out:
            _append_log(
                db, job, LogCode.ERROR_LEAD_OPTED_OUT, {LogParam.LEAD_ID: lead_id}, level="error", visibility="public"
            )
            job.status = "failed"
            job.error = "Lead opted out"
            db.commit()
            return

        first, last, domain = lead.first_name, lead.last_name, lead.domain
        _append_log(
            db,
            job,
            LogCode.DEBUG_LEAD_LOADED,
            {LogParam.LEAD_ID: lead.id, LogParam.DOMAIN: domain, LogParam.FIRST_NAME: first, LogParam.LAST_NAME: last},
            visibility="superadmin",
        )
        db.commit()
        _append_log(db, job, LogCode.VERIFY_DOMAIN, {LogParam.DOMAIN: domain}, visibility="public")
        db.commit()
        _append_log(db, job, LogCode.VERIFY_GENERATING_CANDIDATES, visibility="public")
        db.commit()
        _append_log(db, job, LogCode.VERIFY_CHECKING_MAIL_SERVER, visibility="public")
        cfg = get_workspace_config_sync(db, workspace_id)
        _append_log(
            db,
            job,
            LogCode.DEBUG_CALLING_VERIFIER,
            {LogParam.FIRST_NAME: first, LogParam.LAST_NAME: last, LogParam.DOMAIN: domain},
            visibility="superadmin",
        )
        db.commit()

        # Create logger for verification
        logger = _create_job_logger(db, job)

        def _on_web_search(provider: str) -> None:
            """Callback to track web search usage (Serper)."""
            if provider == "serper":
                from app.services.serper_usage import increment_serper_usage_sync

                try:
                    increment_serper_usage_sync(db, workspace_id)
                except Exception as e:
                    _append_log(db, job, LogCode.DEBUG_MX_EXCEPTION, {LogParam.ERROR: str(e)}, visibility="superadmin")
                    db.commit()

        try:
            candidates, best_email, best_result, probe_results = verify_and_pick_best(
                first,
                last,
                domain,
                mail_from=cfg.get("smtp_mail_from"),
                logger=logger,
                smtp_timeout_seconds=cfg.get("smtp_timeout_seconds"),
                dns_timeout_seconds=cfg.get("dns_timeout_seconds"),
                enabled_pattern_indices=cfg.get("enabled_pattern_indices"),
                web_search_provider=cfg.get("web_search_provider"),
                web_search_api_key=cfg.get("web_search_api_key"),
                allow_no_lastname=cfg.get("allow_no_lastname", False),
                on_web_search_performed=_on_web_search,
                custom_patterns=cfg.get("custom_patterns"),
            )
        except SoftTimeLimitExceeded:
            _mark_job_failed(
                db,
                job_id,
                workspace_id,
                "Execution time exceeded (timeout)",
                code=LogCode.JOB_TIMEOUT,
            )
            return
        except Exception as e:
            err_msg = str(e)[:500]
            _append_log(db, job, LogCode.ERROR_GENERIC, {LogParam.ERROR: err_msg}, level="error", visibility="public")
            job.status = "failed"
            job.error = err_msg
            db.commit()
            raise

        _append_log(
            db,
            job,
            LogCode.DEBUG_VERIFIER_RESULT,
            {LogParam.COUNT: len(candidates), LogParam.EMAIL: best_email or ""},
            visibility="superadmin",
        )
        db.commit()

        mx_hosts = []
        try:
            from app.services.verifier import mx_lookup

            mx_hosts = [h for _, h in mx_lookup(domain, dns_timeout_seconds=cfg.get("dns_timeout_seconds"))]
        except Exception as ex:
            _append_log(
                db,
                job,
                LogCode.DEBUG_MX_EXCEPTION,
                {LogParam.ERROR: f"{type(ex).__name__}: {ex}"},
                visibility="superadmin",
            )
        else:
            _append_log(db, job, LogCode.DEBUG_MX_LOOKUP, {LogParam.COUNT: len(mx_hosts)}, visibility="superadmin")
        db.commit()

        # Log MX/SMTP: public summary; per-candidate detail superadmin only (sensitive emails/statuses)
        if mx_hosts:
            _append_log(db, job, LogCode.VERIFY_MX_RECORDS, {LogParam.HOSTS: ", ".join(mx_hosts)}, visibility="public")
        else:
            _append_log(db, job, LogCode.VERIFY_MX_NOT_FOUND, visibility="public")
        db.commit()
        for i, (email, info) in enumerate(probe_results.items()):
            if i >= MAX_LOGGED_CANDIDATES:
                _append_log(
                    db,
                    job,
                    LogCode.DEBUG_MORE_CANDIDATES,
                    {LogParam.COUNT: len(probe_results) - MAX_LOGGED_CANDIDATES},
                    visibility="superadmin",
                )
                break
            status = info.get("status", "?")
            detail = (info.get("detail") or "")[:100]
            _append_log(
                db,
                job,
                LogCode.DEBUG_CANDIDATE_STATUS,
                {LogParam.EMAIL: email, LogParam.STATUS: status, LogParam.DETAIL: detail},
                visibility="superadmin",
            )
        db.commit()

        log = VerificationLog(
            lead_id=lead.id,
            job_id=job.id,
            mx_hosts=mx_hosts,
            probe_results=probe_results,
            best_email=best_email or "",
            best_status=best_result.status if best_result else "unknown",
            best_confidence=best_result.confidence_score if best_result else 0,
        )
        db.add(log)

        lead.email_candidates = candidates
        lead.email_best = best_email or ""
        lead.verification_status = best_result.status if best_result else "unknown"
        lead.confidence_score = best_result.confidence_score if best_result else 0
        lead.mx_found = best_result.mx_found if best_result else False
        lead.catch_all = best_result.catch_all if best_result else False
        lead.smtp_check = best_result.smtp_check if best_result else False
        lead.notes = best_result.reason if best_result else ""
        lead.web_mentioned = getattr(best_result, "web_mentioned", False) if best_result else False
        lead.updated_at = datetime.now(UTC)

        if lead.email_best:
            _append_log(db, job, LogCode.VERIFY_COMPLETED, {LogParam.EMAIL: lead.email_best}, visibility="public")
        else:
            _append_log(db, job, LogCode.VERIFY_NO_EMAIL_FOUND, visibility="public")
        _append_log(db, job, LogCode.JOB_COMPLETED, {LogParam.LEAD_ID: lead_id}, visibility="public")
        job.status = "succeeded"
        job.progress = 100
        job.result = {
            "lead_id": lead_id,
            "email_best": lead.email_best,
            "verification_status": lead.verification_status,
        }
        db.commit()

        # Increment usage
        period = datetime.now(UTC).strftime("%Y-%m")
        r2 = db.execute(select(Usage).where(Usage.workspace_id == workspace_id, Usage.period == period))
        u = r2.scalars().one_or_none()
        if not u:
            u = Usage(workspace_id=workspace_id, period=period, verifications_count=1, exports_count=0)
            db.add(u)
        else:
            u.verifications_count += 1
        db.commit()

        # Fire webhook verification.completed
        from app.tasks.webhooks import dispatch_webhook_event

        dispatch_webhook_event(
            workspace_id,
            "verification.completed",
            {
                "job_id": job_id,
                "lead_id": lead_id,
                "email_best": lead.email_best,
                "verification_status": lead.verification_status,
                "confidence_score": lead.confidence_score,
            },
        )
    except SoftTimeLimitExceeded:
        _mark_job_failed(
            db,
            job_id,
            workspace_id,
            "Execution time exceeded (timeout)",
        )
        return
    except Exception as e:
        # Mark job as failed if something fails after verify_and_pick_best
        try:
            _mark_job_failed(db, job_id, workspace_id, str(e)[:500])
        except Exception:
            pass
        raise
    finally:
        db.close()
