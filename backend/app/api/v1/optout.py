"""Opt-out: mark lead/email/domain as opt-out."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_workspace_required, require_scope
from app.core.error_codes import ErrorCode
from app.models import Lead, OptOut
from app.schemas.common import APIResponse
from app.schemas.optout import OptOutRequest

router = APIRouter()


@router.post("", response_model=APIResponse, dependencies=[require_scope("optout:write")])
async def opt_out(
    body: OptOutRequest,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    now = datetime.now(UTC)
    if body.lead_id:
        r = await db.execute(select(Lead).where(Lead.id == body.lead_id, Lead.workspace_id == workspace.id))
        lead = r.unique().scalars().one_or_none()
        if not lead:
            return APIResponse.err(ErrorCode.LEAD_NOT_FOUND.value, "Lead not found", {"id": body.lead_id})
        lead.opt_out = True
        lead.opt_out_at = now
        email = lead.email_best or ""
        domain = lead.domain or ""
        rec = OptOut(workspace_id=workspace.id, lead_id=lead.id, email=email, domain=domain, reason=body.reason or "")
        db.add(rec)
    elif body.email:
        domain = (body.email.split("@")[1] if "@" in body.email else "") or body.domain or ""
        rec = OptOut(workspace_id=workspace.id, email=body.email, domain=domain, reason=body.reason or "")
        db.add(rec)
        await db.flush()
        # Mark any lead with this email as opt_out
        r = await db.execute(select(Lead).where(Lead.workspace_id == workspace.id, Lead.email_best == body.email))
        for lead in r.unique().scalars().all():
            lead.opt_out = True
            lead.opt_out_at = now
    elif body.domain:
        rec = OptOut(workspace_id=workspace.id, email="", domain=body.domain, reason=body.reason or "")
        db.add(rec)
        await db.flush()
        r = await db.execute(select(Lead).where(Lead.workspace_id == workspace.id, Lead.domain == body.domain))
        for lead in r.unique().scalars().all():
            lead.opt_out = True
            lead.opt_out_at = now
    else:
        return APIResponse.err(ErrorCode.VALIDATION_REQUIRED_FIELD.value, "Provide lead_id, email, or domain", {})
    await db.commit()
    return APIResponse.ok({"ok": True, "message": "Opt-out recorded"})
