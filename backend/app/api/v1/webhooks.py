"""Webhooks: test, register."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_workspace_required, require_scope
from app.models import Webhook
from app.schemas.common import APIResponse
from app.schemas.webhook import WebhookCreate

router = APIRouter()


@router.post("/test", response_model=APIResponse, dependencies=[require_scope("webhooks:write")])
async def test_webhook(
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Send a test event to verify webhook URL (optional implementation)."""
    return APIResponse.ok({"ok": True, "message": "Webhook test endpoint; implement POST to your URL with test payload"})


@router.post("", response_model=APIResponse, dependencies=[require_scope("webhooks:write")])
async def create_webhook(
    body: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    secret = secrets.token_urlsafe(32)
    events_str = ",".join(body.events)
    wh = Webhook(
        workspace_id=workspace.id,
        url=body.url,
        secret=secret,
        events=events_str,
        is_active=True,
    )
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return APIResponse.ok({
        "id": wh.id,
        "url": wh.url,
        "events": body.events,
        "is_active": wh.is_active,
        "secret": secret,
        "created_at": wh.created_at.isoformat() if wh.created_at else "",
    })


@router.get("", response_model=APIResponse, dependencies=[require_scope("webhooks:write")])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    from sqlalchemy import select
    r = await db.execute(select(Webhook).where(Webhook.workspace_id == workspace.id))
    hooks = r.unique().scalars().all()
    items = [
        {"id": w.id, "url": w.url, "events": w.events.split(",") if w.events else [], "is_active": w.is_active, "created_at": w.created_at.isoformat() if w.created_at else ""}
        for w in hooks
    ]
    return APIResponse.ok({"items": items})
