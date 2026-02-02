"""Workspace verification config: GET/PUT per workspace (key-value table)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_workspace_required, require_scope
from app.models import WorkspaceConfigEntry
from app.schemas.common import APIResponse
from app.schemas.config import (
    MAX_CUSTOM_PATTERNS,
    MAX_PATTERN_LENGTH,
    MAX_TIMEOUT_SECONDS,
    MIN_PATTERNS_ENABLED,
    MIN_TIMEOUT_SECONDS,
    PATTERN_COUNT,
    ConfigUpdate,
)
from app.services.serper_usage import get_serper_usage_async
from app.services.workspace_config import merge_config_for_response

router = APIRouter()


@router.get("", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def get_config(
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Workspace config (merged with globals)."""
    workspace, _, _ = workspace_required
    r = await db.execute(select(WorkspaceConfigEntry).where(WorkspaceConfigEntry.workspace_id == workspace.id))
    entries = list(r.scalars().all())
    return APIResponse.ok(merge_config_for_response(entries))


@router.put("", response_model=APIResponse, dependencies=[require_scope("leads:write")])
async def update_config(
    body: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Updates workspace config. Each key is saved as a record; null/empty = delete (use global)."""
    workspace, _, _ = workspace_required
    r = await db.execute(select(WorkspaceConfigEntry).where(WorkspaceConfigEntry.workspace_id == workspace.id))
    entries_by_key = {e.key: e for e in r.scalars().all()}

    async def set_entry(key: str, value: Any) -> None:
        if value is None or (isinstance(value, str) and not value.strip()):
            if key in entries_by_key:
                await db.delete(entries_by_key[key])
            return
        if isinstance(value, list):
            value = json.dumps(value)
        else:
            value = str(value)
        if key in entries_by_key:
            entries_by_key[key].value = value
        else:
            db.add(WorkspaceConfigEntry(workspace_id=workspace.id, key=key, value=value))

    if body.smtp_timeout_seconds is not None:
        await set_entry(
            "smtp_timeout_seconds", str(max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, body.smtp_timeout_seconds)))
        )
    if body.dns_timeout_seconds is not None:
        await set_entry(
            "dns_timeout_seconds", str(max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, body.dns_timeout_seconds)))
        )
    if body.enabled_pattern_indices is not None:
        indices = [i for i in body.enabled_pattern_indices if 0 <= i < PATTERN_COUNT]
        if len(indices) < MIN_PATTERNS_ENABLED:
            return APIResponse.err(
                "VALIDATION_ERROR",
                f"Debe haber al menos {MIN_PATTERNS_ENABLED} patrones habilitados.",
                {"enabled_pattern_indices": indices},
            )
        await set_entry("enabled_pattern_indices", sorted(set(indices)))
    if body.smtp_mail_from is not None:
        v = body.smtp_mail_from.strip() if isinstance(body.smtp_mail_from, str) else ""
        await set_entry("smtp_mail_from", v if v else None)
    if body.web_search_provider is not None:
        v = body.web_search_provider.strip().lower() if isinstance(body.web_search_provider, str) else ""
        if v and v not in ("bing", "serper"):
            return APIResponse.err(
                "VALIDATION_ERROR", "web_search_provider debe ser 'bing', 'serper' o vacío.", {"web_search_provider": v}
            )
        await set_entry("web_search_provider", v if v else None)
    if body.web_search_api_key is not None:
        v = body.web_search_api_key.strip() if isinstance(body.web_search_api_key, str) else ""
        await set_entry("web_search_api_key", v if v else None)
    if body.allow_no_lastname is not None:
        await set_entry("allow_no_lastname", "true" if body.allow_no_lastname else None)
    if body.custom_patterns is not None:
        # Validate patterns: must contain @{domain} and not exceed limit
        valid_patterns = []
        for p in body.custom_patterns:
            p = p.strip() if isinstance(p, str) else ""
            if p and "@{domain}" in p and len(p) <= MAX_PATTERN_LENGTH:
                valid_patterns.append(p)
        if valid_patterns:
            await set_entry("custom_patterns", valid_patterns[:MAX_CUSTOM_PATTERNS])
        else:
            await set_entry("custom_patterns", None)  # Borrar si lista vacía

    await db.commit()
    r = await db.execute(select(WorkspaceConfigEntry).where(WorkspaceConfigEntry.workspace_id == workspace.id))
    entries = list(r.scalars().all())
    return APIResponse.ok(merge_config_for_response(entries))


@router.get("/serper-usage", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def get_serper_usage(
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Obtiene el uso de Serper.dev para el workspace actual."""
    workspace, _, _ = workspace_required
    usage = await get_serper_usage_async(db, workspace.id)
    return APIResponse.ok(usage)
