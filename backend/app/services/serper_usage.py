"""Tracking de uso de Serper.dev API por workspace."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WorkspaceConfigEntry

# Clave en workspace_config_entries para guardar el uso
SERPER_USAGE_KEY = "serper_usage"


def _get_current_month_key() -> str:
    """Devuelve la clave del mes actual en formato YYYY-MM."""
    return datetime.now(UTC).strftime("%Y-%m")


def _parse_usage_data(raw: str | None) -> dict[str, int]:
    """Parsea el JSON de uso. Formato: {"YYYY-MM": count, ...}"""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {k: int(v) for k, v in data.items() if isinstance(v, (int, float))}
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return {}


def get_serper_usage_sync(db: Session, workspace_id: int) -> dict[str, int]:
    """
    Obtiene el uso de Serper para el workspace.
    Devuelve: {"current_month": count, "total": count, "month_key": "YYYY-MM"}
    """
    r = db.execute(
        select(WorkspaceConfigEntry).where(
            WorkspaceConfigEntry.workspace_id == workspace_id,
            WorkspaceConfigEntry.key == SERPER_USAGE_KEY,
        )
    )
    entry = r.scalars().first()
    usage_data = _parse_usage_data(entry.value if entry else None)

    month_key = _get_current_month_key()
    current_month = usage_data.get(month_key, 0)
    total = sum(usage_data.values())

    return {
        "current_month": current_month,
        "total": total,
        "month_key": month_key,
    }


def increment_serper_usage_sync(db: Session, workspace_id: int) -> int:
    """
    Incrementa el contador de uso de Serper para el workspace.
    Devuelve el nuevo total del mes actual.
    """
    r = db.execute(
        select(WorkspaceConfigEntry).where(
            WorkspaceConfigEntry.workspace_id == workspace_id,
            WorkspaceConfigEntry.key == SERPER_USAGE_KEY,
        )
    )
    entry = r.scalars().first()
    usage_data = _parse_usage_data(entry.value if entry else None)

    month_key = _get_current_month_key()
    usage_data[month_key] = usage_data.get(month_key, 0) + 1

    new_value = json.dumps(usage_data)

    if entry:
        entry.value = new_value
    else:
        db.add(
            WorkspaceConfigEntry(
                workspace_id=workspace_id,
                key=SERPER_USAGE_KEY,
                value=new_value,
            )
        )

    db.commit()
    return usage_data[month_key]


# Versiones async para los endpoints
async def get_serper_usage_async(db, workspace_id: int) -> dict[str, int]:
    """Versión async de get_serper_usage_sync."""

    r = await db.execute(
        select(WorkspaceConfigEntry).where(
            WorkspaceConfigEntry.workspace_id == workspace_id,
            WorkspaceConfigEntry.key == SERPER_USAGE_KEY,
        )
    )
    entry = r.scalars().first()
    usage_data = _parse_usage_data(entry.value if entry else None)

    month_key = _get_current_month_key()
    current_month = usage_data.get(month_key, 0)
    total = sum(usage_data.values())

    return {
        "current_month": current_month,
        "total": total,
        "month_key": month_key,
    }
