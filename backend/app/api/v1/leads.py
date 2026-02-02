"""Leads: CRUD, bulk upsert, list with filters."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    filter_log_lines_for_user,
    get_current_user_optional,
    get_db,
    get_workspace_required,
    is_superadmin,
    require_scope,
)
from app.models import Job, JobLogLine, Lead, User
from app.schemas.common import APIResponse
from app.schemas.lead import LeadBulkRequest, LeadCreate, LeadResponse, LeadUpdate
from app.services.utils import utc_now_iso

router = APIRouter()


def _lead_to_response(lead: Lead, last_job_status: str | None = None) -> dict:
    return LeadResponse(
        id=lead.id,
        workspace_id=lead.workspace_id,
        owner_user_id=lead.owner_user_id,
        first_name=lead.first_name,
        last_name=lead.last_name,
        title=lead.title,
        company=lead.company,
        domain=lead.domain,
        linkedin_url=lead.linkedin_url,
        email_best=lead.email_best,
        email_candidates=lead.email_candidates if isinstance(lead.email_candidates, list) else None,
        verification_status=lead.verification_status,
        confidence_score=lead.confidence_score,
        mx_found=lead.mx_found,
        catch_all=lead.catch_all,
        smtp_check=lead.smtp_check,
        notes=lead.notes,
        web_mentioned=lead.web_mentioned,
        tags=lead.tags,
        sales_status=lead.sales_status,
        source=lead.source,
        lawful_basis=lead.lawful_basis,
        purpose=lead.purpose,
        collected_at=lead.collected_at,
        opt_out=lead.opt_out,
        opt_out_at=lead.opt_out_at,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        last_job_status=last_job_status,
    ).model_dump()


def _normalize(s: str) -> str:
    return (s or "").strip().lower()


def _dedupe_key(lead: Lead) -> tuple:
    return (
        _normalize(lead.domain),
        _normalize(lead.first_name),
        _normalize(lead.last_name),
        _normalize(lead.company),
    )


@router.post("", response_model=APIResponse, dependencies=[require_scope("leads:write")])
async def create_lead(
    body: LeadCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, wu, api_key = workspace_required
    if not api_key and not wu:
        raise HTTPException(401, "Not authenticated")
    # Idempotency
    key = idempotency_key or f"lead-create-{body.linkedin_url or body.domain}-{body.first_name}-{body.last_name}"
    from app.api.deps import check_idempotency, save_idempotency

    cached = await check_idempotency(workspace.id, key, db)
    if cached:
        import json

        return APIResponse.model_validate(json.loads(cached[1]))

    now = utc_now_iso()
    collected_at = datetime.now(UTC) if body.source else None
    lead = Lead(
        workspace_id=workspace.id,
        owner_user_id=wu.user_id if wu else None,
        first_name=body.first_name or "",
        last_name=body.last_name or "",
        title=body.title or "",
        company=body.company or "",
        domain=body.domain or "",
        linkedin_url=body.linkedin_url or "",
        source=body.source or "",
        lawful_basis=body.lawful_basis or "legitimate_interest",
        purpose=body.purpose or "b2b_sales_outreach",
        collected_at=collected_at,
        tags=body.tags,
        sales_status=body.sales_status or "New",
    )
    # Upsert by linkedin_url or (domain + first + last + company)
    if body.linkedin_url:
        r = await db.execute(
            select(Lead).where(Lead.workspace_id == workspace.id, Lead.linkedin_url == body.linkedin_url.strip())
        )
        existing = r.unique().scalars().one_or_none()
    else:
        r = await db.execute(
            select(Lead).where(
                Lead.workspace_id == workspace.id,
                Lead.domain == _normalize(body.domain),
                Lead.first_name == _normalize(body.first_name),
                Lead.last_name == _normalize(body.last_name),
                Lead.company == _normalize(body.company),
            )
        )
        existing = r.unique().scalars().one_or_none()
    if existing:
        existing.first_name = body.first_name or existing.first_name
        existing.last_name = body.last_name or existing.last_name
        existing.title = body.title or existing.title
        existing.company = body.company or existing.company
        existing.domain = body.domain or existing.domain
        existing.linkedin_url = body.linkedin_url or existing.linkedin_url
        existing.source = body.source or existing.source
        existing.updated_at = datetime.fromisoformat(now.replace("Z", "+00:00"))
        await db.flush()
        await db.refresh(existing)
        out = _lead_to_response(existing)
    else:
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        out = _lead_to_response(lead)
    resp = APIResponse.ok(out)
    await save_idempotency(db, workspace.id, key, "", 200, resp.model_dump_json())
    return resp


@router.post("/bulk", response_model=APIResponse, dependencies=[require_scope("leads:write")])
async def bulk_upsert_leads(
    body: LeadBulkRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, wu, api_key = workspace_required
    if not api_key and not wu:
        raise HTTPException(401, "Not authenticated")
    # idempotency_key is accepted but not used for bulk operations
    _ = idempotency_key
    created = 0
    updated = 0
    ids = []
    for item in body.leads:
        r = await db.execute(
            select(Lead).where(
                Lead.workspace_id == workspace.id,
                Lead.linkedin_url == (item.linkedin_url or "").strip(),
            )
        )
        ex = r.unique().scalars().one_or_none()
        if not ex and not item.linkedin_url:
            r2 = await db.execute(
                select(Lead).where(
                    Lead.workspace_id == workspace.id,
                    Lead.domain == _normalize(item.domain),
                    Lead.first_name == _normalize(item.first_name),
                    Lead.last_name == _normalize(item.last_name),
                    Lead.company == _normalize(item.company),
                )
            )
            ex = r2.unique().scalars().one_or_none()
        now = datetime.now(UTC)
        if ex:
            ex.first_name = item.first_name or ex.first_name
            ex.last_name = item.last_name or ex.last_name
            ex.domain = item.domain or ex.domain
            ex.company = item.company or ex.company
            ex.linkedin_url = item.linkedin_url or ex.linkedin_url
            ex.source = item.source or ex.source
            ex.updated_at = now
            updated += 1
            ids.append(ex.id)
        else:
            lead = Lead(
                workspace_id=workspace.id,
                owner_user_id=wu.user_id if wu else None,
                first_name=item.first_name or "",
                last_name=item.last_name or "",
                company=item.company or "",
                domain=item.domain or "",
                linkedin_url=item.linkedin_url or "",
                source=item.source or "",
                lawful_basis=item.lawful_basis or "legitimate_interest",
                purpose=item.purpose or "b2b_sales_outreach",
                collected_at=now,
            )
            db.add(lead)
            await db.flush()
            await db.refresh(lead)
            created += 1
            ids.append(lead.id)
    await db.commit()
    return APIResponse.ok({"created": created, "updated": updated, "ids": ids})


@router.post("/{lead_id}/verify", response_model=APIResponse, dependencies=[require_scope("verify:run")])
async def enqueue_verify_lead(
    lead_id: int,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Enqueue verification for lead. Returns job_id. Poll GET /v1/jobs/{job_id}."""
    import uuid

    workspace, _, _ = workspace_required
    from app.services.usage_plan import check_verification_quota

    quota_err = await check_verification_quota(db, workspace)
    if quota_err:
        return APIResponse.err("QUOTA_EXCEEDED", quota_err, {"code": "quota_exceeded"})
    r = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.workspace_id == workspace.id))
    lead = r.unique().scalars().one_or_none()
    if not lead:
        return APIResponse.err("NOT_FOUND", "Lead not found", {"id": lead_id})
    if lead.opt_out:
        return APIResponse.err("OPT_OUT", "Lead has opted out", {"id": lead_id})
    job_id = str(uuid.uuid4())
    from app.models import Job

    job = Job(workspace_id=workspace.id, lead_id=lead_id, job_id=job_id, kind="verify", status="queued", progress=0)
    db.add(job)
    await db.commit()
    from app.tasks.verify import run_verify_lead

    run_verify_lead.delay(lead_id, workspace.id, job_id)
    return APIResponse.ok({"job_id": job_id})


def _verification_log_entries_filter(rows: list, current_user: User | None) -> tuple[list, list]:
    """Given a list of JobLogLine (ordered by seq), returns (log_lines, log_entries) filtering by visibility: superadmin only if user is superadmin."""
    visible = [
        r for r in rows if r.visibility == "public" or (r.visibility == "superadmin" and is_superadmin(current_user))
    ]
    entries = [
        {"created_at": (r.created_at.isoformat() if r.created_at else None), "message": r.message} for r in visible
    ]
    log_lines = [e["message"] for e in entries]
    return log_lines, entries


@router.get("/{lead_id}/verification-log", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def get_lead_verification_log(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
    current_user: User | None = Depends(get_current_user_optional),
) -> APIResponse:
    """Returns the last verification job for this lead (job_id, status, log_lines, log_entries with timestamp, created_at, error). Superadmin sees [DEBUG] lines."""
    workspace, _, _ = workspace_required
    r = await db.execute(
        select(Job)
        .where(Job.workspace_id == workspace.id, Job.lead_id == lead_id, Job.kind == "verify")
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    job = r.unique().scalars().one_or_none()
    if not job:
        return APIResponse.err("NOT_FOUND", "No verification log for this lead", {"lead_id": lead_id})
    r2 = await db.execute(select(JobLogLine).where(JobLogLine.job_id == job.id).order_by(JobLogLine.seq))
    rows = r2.unique().scalars().all()
    if rows:
        log_lines, log_entries = _verification_log_entries_filter(rows, current_user)
    else:
        log_lines = filter_log_lines_for_user(job.log_lines, current_user)
        log_entries = []
    return APIResponse.ok(
        {
            "job_id": job.job_id,
            "status": job.status,
            "log_lines": log_lines,
            "log_entries": log_entries,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "error": job.error or None,
        }
    )


@router.patch("/{lead_id}", response_model=APIResponse, dependencies=[require_scope("leads:write")])
async def update_lead(
    lead_id: int,
    body: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Updates lead fields (only provided ones, ignores null)."""
    workspace, _, _ = workspace_required
    r = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.workspace_id == workspace.id))
    lead = r.unique().scalars().one_or_none()
    if not lead:
        return APIResponse.err("NOT_FOUND", "Lead not found", {"id": lead_id})
    # Actualizar solo campos proporcionados
    if body.first_name is not None:
        lead.first_name = body.first_name.strip()
    if body.last_name is not None:
        lead.last_name = body.last_name.strip()
    if body.title is not None:
        lead.title = body.title.strip()
    if body.company is not None:
        lead.company = body.company.strip()
    if body.domain is not None:
        lead.domain = body.domain.strip().lower()
    if body.linkedin_url is not None:
        lead.linkedin_url = body.linkedin_url.strip()
    if body.tags is not None:
        lead.tags = body.tags
    if body.sales_status is not None:
        lead.sales_status = body.sales_status.strip()
    if body.owner_user_id is not None:
        lead.owner_user_id = body.owner_user_id
    lead.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(lead)
    return APIResponse.ok(_lead_to_response(lead))


@router.get("/{lead_id}", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    r = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.workspace_id == workspace.id))
    lead = r.unique().scalars().one_or_none()
    if not lead:
        return APIResponse.err("NOT_FOUND", "Lead not found", {"id": lead_id})
    return APIResponse.ok(_lead_to_response(lead))


@router.get("", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def list_leads(
    page: int = 1,
    page_size: int = 20,
    domain: str | None = None,
    verification_status: str | None = None,
    sales_status: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    q = select(Lead).where(Lead.workspace_id == workspace.id)
    if domain:
        q = q.where(Lead.domain.ilike(f"%{domain}%"))
    if verification_status:
        q = q.where(Lead.verification_status == verification_status)
    if sales_status:
        q = q.where(Lead.sales_status == sales_status)
    if search:
        q = q.where(
            Lead.first_name.ilike(f"%{search}%")
            | Lead.last_name.ilike(f"%{search}%")
            | Lead.company.ilike(f"%{search}%")
            | Lead.email_best.ilike(f"%{search}%")
        )
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.offset((page - 1) * page_size).limit(page_size).order_by(Lead.updated_at.desc())
    result = await db.execute(q)
    leads = result.unique().scalars().all()

    # Obtener el estado del último job de verificación para cada lead
    lead_ids = [lead.id for lead in leads]
    last_job_status_map: dict[int, str] = {}
    if lead_ids:
        # Obtener los últimos jobs de verificación para estos leads (ordenados por fecha desc)
        # Agrupamos manualmente para compatibilidad con SQLite y PostgreSQL
        jobs_q = (
            select(Job)
            .where(Job.workspace_id == workspace.id, Job.lead_id.in_(lead_ids), Job.kind == "verify")
            .order_by(Job.created_at.desc())
        )
        jobs_result = await db.execute(jobs_q)
        for job in jobs_result.unique().scalars().all():
            # Solo guardamos el primero (más reciente) por lead_id
            if job.lead_id not in last_job_status_map:
                last_job_status_map[job.lead_id] = job.status

    items = [_lead_to_response(lead, last_job_status_map.get(lead.id)) for lead in leads]
    return APIResponse.ok({"items": items}, meta={"page": page, "page_size": page_size, "total": total})
