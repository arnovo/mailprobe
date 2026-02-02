"""Exports: request CSV export (async), get job_id."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_workspace_required, require_scope
from app.models import Job
from app.schemas.common import APIResponse

router = APIRouter()


@router.post("/csv", response_model=APIResponse, dependencies=[require_scope("exports:run")])
async def export_csv(
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Request CSV export (async). Returns job_id. Poll GET /jobs/{job_id} for result."""
    workspace, _, _ = workspace_required
    key = idempotency_key or f"export-csv-{uuid.uuid4()}"
    from app.api.deps import check_idempotency, save_idempotency

    cached = await check_idempotency(workspace.id, key, db)
    if cached:
        import json

        return APIResponse.model_validate(json.loads(cached[1]))
    job_id = str(uuid.uuid4())
    job = Job(workspace_id=workspace.id, job_id=job_id, kind="export_csv", status="queued", progress=0)
    db.add(job)
    await db.commit()
    from app.tasks.exports import run_export_csv

    run_export_csv.delay(workspace.id, job_id)
    resp = APIResponse.ok({"job_id": job_id})
    await save_idempotency(db, workspace.id, key, "", 200, resp.model_dump_json())
    return resp
