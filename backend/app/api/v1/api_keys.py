"""API Keys: create, list, revoke."""

from __future__ import annotations

from datetime import UTC

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_workspace_required, require_scope
from app.core.security import full_api_key, generate_api_key_prefix, generate_api_key_secret, hash_api_key
from app.models import ApiKey
from app.schemas.auth import ApiKeyCreate
from app.schemas.common import APIResponse

router = APIRouter()


@router.post("", response_model=APIResponse, dependencies=[require_scope("webhooks:write")])
async def create_api_key(
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    from app.services.usage_plan import get_plan_limits

    _, max_keys = get_plan_limits(workspace.plan)
    r = await db.execute(select(ApiKey).where(ApiKey.workspace_id == workspace.id, ApiKey.revoked_at.is_(None)))
    count = len(r.unique().scalars().all())
    if count >= max_keys:
        return APIResponse.err("QUOTA_EXCEEDED", f"Max API keys for plan: {max_keys}", {"max": max_keys})
    prefix = generate_api_key_prefix()
    secret = generate_api_key_secret()
    full = full_api_key(prefix, secret)
    key_hash = hash_api_key(full)
    scopes_str = ",".join(body.scopes)
    from app.core.config import settings

    rate = getattr(settings, "rate_limit_per_key", 60)
    key = ApiKey(
        workspace_id=workspace.id,
        name=body.name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=scopes_str,
        rate_limit_per_minute=rate,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return APIResponse.ok(
        {
            "id": key.id,
            "name": key.name,
            "key_prefix": key.key_prefix,
            "key": full,
            "scopes": body.scopes,
            "rate_limit_per_minute": key.rate_limit_per_minute,
            "created_at": key.created_at.isoformat() if key.created_at else "",
        }
    )


@router.get("", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    r = await db.execute(select(ApiKey).where(ApiKey.workspace_id == workspace.id))
    keys = r.unique().scalars().all()
    items = [
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "scopes": k.scopes.split(",") if k.scopes else [],
            "rate_limit_per_minute": k.rate_limit_per_minute,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else "",
            "revoked_at": k.revoked_at.isoformat() if k.revoked_at else None,
        }
        for k in keys
    ]
    return APIResponse.ok({"items": items})


@router.delete("/{key_id}", response_model=APIResponse, dependencies=[require_scope("webhooks:write")])
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    from datetime import datetime

    r = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.workspace_id == workspace.id))
    key = r.unique().scalars().one_or_none()
    if not key:
        return APIResponse.err("NOT_FOUND", "API key not found", {"id": key_id})
    key.revoked_at = datetime.now(UTC)
    await db.commit()
    return APIResponse.ok({"ok": True})
