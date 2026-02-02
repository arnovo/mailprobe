"""Jobs: list active jobs, get job status, cancel (superadmin)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    filter_log_lines_for_user,
    get_current_user_optional,
    get_db,
    get_workspace_required,
    is_superadmin,
    require_scope,
    require_superadmin,
)
from app.models import Job, JobLogLine, User
from app.schemas.common import APIResponse, JobListItem, JobStatus

router = APIRouter()


@router.get("", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def list_jobs(
    active_only: bool = Query(False, description="Si true, solo jobs en estado queued o running"),
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Lista jobs del workspace del usuario. Con active_only=true solo devuelve los activos (queued|running)."""
    workspace, _, _ = workspace_required
    q = select(Job).where(Job.workspace_id == workspace.id).order_by(Job.created_at.desc())
    if active_only:
        q = q.where(Job.status.in_(["queued", "running"]))
    r = await db.execute(q)
    jobs = r.unique().scalars().all()
    items = [
        JobListItem(
            job_id=j.job_id,
            kind=j.kind,
            status=j.status,
            progress=j.progress or 0,
            lead_id=j.lead_id,
            created_at=j.created_at.isoformat() if j.created_at else None,
        )
        for j in jobs
    ]
    return APIResponse.ok({"jobs": items})


@router.post("/{job_id}/cancel", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
    _superadmin: User = Depends(require_superadmin()),
) -> APIResponse:
    """Cancela un job (solo superadmin). El job debe estar en queued o running."""
    workspace, _, _ = workspace_required
    r = await db.execute(
        select(Job).where(Job.job_id == job_id, Job.workspace_id == workspace.id)
    )
    job = r.unique().scalars().one_or_none()
    if not job:
        return APIResponse.err("NOT_FOUND", "Job not found", {"job_id": job_id})
    if job.status not in ("queued", "running"):
        return APIResponse.err("INVALID_STATE", f"Cannot cancel job in state {job.status}", {"job_id": job_id})
    job.status = "cancelled"
    if job.log_lines is None:
        job.log_lines = []
    msg = "Job cancelado por superadmin."
    job.log_lines.append(msg)
    db.add(JobLogLine(job_id=job.id, seq=len(job.log_lines) - 1, message=msg, level="info", visibility="public"))
    await db.commit()
    return APIResponse.ok({"job_id": job_id, "status": "cancelled"})


def _job_log_entries_filter(rows: list, current_user: User | None) -> tuple[list[str], list[dict]]:
    """Dado lista de JobLogLine (ordenada por seq), devuelve (log_lines, log_entries) filtrando por visibility: superadmin solo si user es superadmin."""
    visible = [r for r in rows if r.visibility == "public" or (r.visibility == "superadmin" and is_superadmin(current_user))]
    entries = [{"created_at": (r.created_at.isoformat() if r.created_at else None), "message": r.message} for r in visible]
    log_lines = [e["message"] for e in entries]
    return log_lines, entries


@router.get("/{job_id}", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
    current_user: User | None = Depends(get_current_user_optional),
) -> APIResponse:
    workspace, _, _ = workspace_required
    r = await db.execute(
        select(Job).where(Job.job_id == job_id, Job.workspace_id == workspace.id)
    )
    job = r.unique().scalars().one_or_none()
    if not job:
        return APIResponse.err("NOT_FOUND", "Job not found", {"job_id": job_id})
    r2 = await db.execute(
        select(JobLogLine).where(JobLogLine.job_id == job.id).order_by(JobLogLine.seq)
    )
    rows = r2.unique().scalars().all()
    if rows:
        log_lines, log_entries = _job_log_entries_filter(rows, current_user)
        out = JobStatus(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            result=job.result,
            error=job.error or None,
            log_lines=log_lines or None,
        ).model_dump()
        out["log_entries"] = log_entries
    else:
        log_lines = filter_log_lines_for_user(job.log_lines, current_user)
        out = JobStatus(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            result=job.result,
            error=job.error or None,
            log_lines=log_lines or None,
        ).model_dump()
        out["log_entries"] = []
    return APIResponse.ok(out)
