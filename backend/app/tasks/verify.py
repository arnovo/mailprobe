"""Celery task: verify lead (find candidates + verify + update lead)."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Sync engine for Celery (worker runs outside async)
from app.core.config import settings as s
from app.services.verifier import verify_and_pick_best
from app.services.workspace_config import get_workspace_config_sync
from app.tasks.celery_app import celery_app

if TYPE_CHECKING:
    from app.models import Job

engine = create_engine(s.database_url_sync, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)

# Verificación puede tardar mucho (DNS, varios MX, SMTP por candidato). Límite por tarea: 10 min soft, 11 min hard.
VERIFY_SOFT_TIME_LIMIT = 600
VERIFY_TIME_LIMIT = 660


def get_sync_session() -> Session:
    return SessionLocal()


def _log_level(message: str) -> str:
    if message.strip().startswith("[DEBUG]"):
        return "debug"
    if "Error" in message or "error" in message.lower():
        return "error"
    return "info"


def _append_log(
    db: Session,
    job: Job,
    message: str,
    level: str | None = None,
    visibility: str | None = None,
) -> None:
    """Añade una línea al job (JSON log_lines) y a la tabla job_log_lines.
    visibility: "public" (todos) o "superadmin" (solo superadmin; logs más detallados/comprometedores).
    Requiere migraciones 004 y 005 aplicadas (tabla job_log_lines y columna visibility).
    """
    from app.models import JobLogLine
    job.log_lines = (job.log_lines or []) + [message]
    seq = len(job.log_lines) - 1
    lvl = level or _log_level(message)
    if visibility is None:
        visibility = "superadmin" if message.strip().startswith("[DEBUG]") else "public"
    db.add(JobLogLine(job_id=job.id, seq=seq, message=message, level=lvl, visibility=visibility))


def _mark_job_failed(db: Session, job_id: str, workspace_id: int, reason: str) -> None:
    """Actualiza el job a failed y hace commit."""
    from app.models import Job
    r = db.execute(select(Job).where(Job.job_id == job_id, Job.workspace_id == workspace_id))
    job = r.scalars().one_or_none()
    if job:
        _append_log(db, job, f"Error detectado: {reason}", level="error", visibility="public")
        job.status = "failed"
        job.error = reason[:500]
        db.commit()


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
        _append_log(db, job, f"Job iniciado — tipo: verify, lead_id: {lead_id}, workspace_id: {workspace_id}", visibility="public")
        _append_log(db, job, "Iniciando verificación...", visibility="public")
        _append_log(db, job, f"[DEBUG] Worker procesando job_id={job_id}, lead_id={lead_id}, workspace_id={workspace_id}", visibility="superadmin")
        db.commit()

        r = db.execute(select(Lead).where(Lead.id == lead_id, Lead.workspace_id == workspace_id))
        lead = r.scalars().one_or_none()
        if not lead or lead.opt_out:
            _append_log(db, job, "Error detectado: Lead no encontrado o con opt-out.", level="error", visibility="public")
            job.status = "failed"
            job.error = "Lead not found or opted out"
            db.commit()
            return

        first, last, domain = lead.first_name, lead.last_name, lead.domain
        _append_log(db, job, f"[DEBUG] Lead cargado: id={lead.id}, domain={domain!r}, first={first!r}, last={last!r}", visibility="superadmin")
        db.commit()
        _append_log(db, job, "Verificando dominio...", visibility="public")
        db.commit()
        _append_log(db, job, "Generando candidatos de email...", visibility="public")
        db.commit()
        _append_log(db, job, "Comprobando servidor de correo (MX/SMTP)...", visibility="public")
        cfg = get_workspace_config_sync(db, workspace_id)
        _append_log(db, job, f"[DEBUG] Llamando verify_and_pick_best(first={first!r}, last={last!r}, domain={domain!r}) con config workspace...", visibility="superadmin")
        db.commit()

        def _progress_cb(msg: str | None, candidate_email: str | None = None, smtp_response: str | None = None) -> None:
            if msg:
                _append_log(db, job, msg, visibility="public")
            if candidate_email:
                _append_log(db, job, f"  Candidato: {candidate_email}", visibility="superadmin")
            if smtp_response:
                _append_log(db, job, f"  SMTP: {smtp_response}", visibility="superadmin")
            db.commit()

        def _detail_cb(detail_msg: str) -> None:
            _append_log(db, job, detail_msg, visibility="superadmin")
            db.commit()

        def _on_web_search(provider: str) -> None:
            """Callback para trackear uso de búsqueda web (Serper)."""
            if provider == "serper":
                from app.services.serper_usage import increment_serper_usage_sync
                try:
                    increment_serper_usage_sync(db, workspace_id)
                except Exception as e:
                    _append_log(db, job, f"[DEBUG] Error tracking Serper usage: {e}", visibility="superadmin")
                    db.commit()

        try:
            candidates, best_email, best_result, probe_results = verify_and_pick_best(
                first, last, domain,
                mail_from=cfg.get("smtp_mail_from"),
                progress_callback=_progress_cb,
                detail_callback=_detail_cb,
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
            _mark_job_failed(db, job_id, workspace_id, "Tiempo de ejecución excedido (timeout). La verificación tardó más de lo permitido.")
            return
        except Exception as e:
            err_msg = str(e)[:500]
            _append_log(db, job, f"Error detectado: {err_msg}", level="error", visibility="public")
            job.status = "failed"
            job.error = err_msg
            db.commit()
            raise

        _append_log(db, job, f"[DEBUG] verify_and_pick_best retornó: {len(candidates)} candidatos, best_email={best_email!r}", visibility="superadmin")
        db.commit()

        mx_hosts = []
        try:
            from app.services.verifier import mx_lookup
            mx_hosts = [h for _, h in mx_lookup(domain, dns_timeout_seconds=cfg.get("dns_timeout_seconds"))]
        except Exception as ex:
            _append_log(db, job, f"[DEBUG] mx_lookup excepción: {type(ex).__name__}: {ex}", visibility="superadmin")
        else:
            _append_log(db, job, f"[DEBUG] mx_lookup: {len(mx_hosts)} hosts", visibility="superadmin")
        db.commit()

        # Log MX/SMTP: resumen público; detalle por candidato solo superadmin (emails/estados más comprometedores)
        _append_log(db, job, "Registros MX: " + (", ".join(mx_hosts) if mx_hosts else "(no encontrados)"), visibility="public")
        db.commit()
        for i, (email, info) in enumerate(probe_results.items()):
            if i >= 15:
                _append_log(db, job, f"  ... y {len(probe_results) - 15} candidatos más", visibility="superadmin")
                break
            status = info.get("status", "?")
            detail = (info.get("detail") or "")[:100]
            _append_log(db, job, f"  {email}: {status} — {detail}", visibility="superadmin")
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

        _append_log(db, job, f"Verificación completada. Mejor email: {lead.email_best or '(ninguno)'}", visibility="public")
        job.status = "succeeded"
        job.progress = 100
        job.result = {"lead_id": lead_id, "email_best": lead.email_best, "verification_status": lead.verification_status}
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
        dispatch_webhook_event(workspace_id, "verification.completed", {
            "job_id": job_id,
            "lead_id": lead_id,
            "email_best": lead.email_best,
            "verification_status": lead.verification_status,
            "confidence_score": lead.confidence_score,
        })
    except SoftTimeLimitExceeded:
        _mark_job_failed(db, job_id, workspace_id, "Tiempo de ejecución excedido (timeout). La verificación tardó más de lo permitido.")
        return
    except Exception as e:
        # Marcar job como failed si falla algo después de verify_and_pick_best
        try:
            _mark_job_failed(db, job_id, workspace_id, str(e)[:500])
        except Exception:
            pass
        raise
    finally:
        db.close()
