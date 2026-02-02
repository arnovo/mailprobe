"""Workspace config: clave-valor (entries). Merge con valores globales."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import WorkspaceConfigEntry
from app.services.email_patterns import COMMON_PATTERNS

# Límites (coinciden con schemas/config.py)
MAX_TIMEOUT_SECONDS = 30
MIN_TIMEOUT_SECONDS = 1
MIN_PATTERNS_ENABLED = 5
PATTERN_COUNT = 10

# Claves conocidas y cómo parsear el valor. Añadir aquí nuevas claves sin migración.
# web_search_provider: 'bing' | 'serper' | '' (vacío = no buscar)
# web_search_api_key: clave del provider
# allow_no_lastname: permite generar candidatos cuando no hay apellido (info@, contact@, etc.)
# custom_patterns: patrones adicionales definidos por el workspace (lista JSON de strings)
CONFIG_KEYS = {
    "smtp_timeout_seconds": {"type": int, "default": lambda: getattr(settings, "smtp_timeout_seconds", 5)},
    "dns_timeout_seconds": {"type": float, "default": lambda: getattr(settings, "dns_timeout_seconds", 5.0)},
    "enabled_pattern_indices": {"type": "json_list_int", "default": lambda: list(range(PATTERN_COUNT))},
    "smtp_mail_from": {"type": str, "default": lambda: getattr(settings, "smtp_mail_from", "noreply@mailcheck.local")},
    "web_search_provider": {"type": str, "default": lambda: ""},
    "web_search_api_key": {"type": str, "default": lambda: ""},
    "allow_no_lastname": {"type": bool, "default": lambda: False},
    "custom_patterns": {"type": "json_list_str", "default": lambda: []},
}


MAX_CUSTOM_PATTERNS = 20  # Límite de patrones personalizados por workspace


def _parse_value(key: str, raw: str) -> Any:
    spec = CONFIG_KEYS.get(key)
    if not spec:
        return raw
    t = spec["type"]
    if t is int:
        return max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, int(raw)))
    if t is float:
        return max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, float(raw)))
    if t == "json_list_int":
        indices = json.loads(raw)
        if not isinstance(indices, list) or len(indices) < MIN_PATTERNS_ENABLED:
            return list(range(PATTERN_COUNT))
        return [i for i in indices if isinstance(i, int) and 0 <= i < PATTERN_COUNT][:PATTERN_COUNT]
    if t == "json_list_str":
        patterns = json.loads(raw)
        if not isinstance(patterns, list):
            return []
        # Validar y limpiar patrones: deben contener {first}, {last}, {f}, {l} o {domain}
        valid = []
        for p in patterns:
            if isinstance(p, str) and "@{domain}" in p and len(p) <= 100:
                valid.append(p.strip())
        return valid[:MAX_CUSTOM_PATTERNS]
    return raw


def get_workspace_config_sync(db: Session, workspace_id: int) -> dict[str, Any]:
    """
    Devuelve la config del workspace fusionada con globales.
    Lee todos los registros de workspace_config_entries para ese workspace y aplica tipos/defaults.
    Keys: smtp_timeout_seconds, dns_timeout_seconds, enabled_pattern_indices, smtp_mail_from.
    """
    r = db.execute(
        select(WorkspaceConfigEntry).where(WorkspaceConfigEntry.workspace_id == workspace_id)
    )
    entries = list(r.scalars().all())
    raw: dict[str, str] = {e.key: e.value for e in entries}

    smtp = getattr(settings, "smtp_timeout_seconds", 5)
    dns = getattr(settings, "dns_timeout_seconds", 5.0)
    mail_from = getattr(settings, "smtp_mail_from", "noreply@mailcheck.local")
    indices: list[int] = list(range(PATTERN_COUNT))

    if "smtp_timeout_seconds" in raw:
        smtp = _parse_value("smtp_timeout_seconds", raw["smtp_timeout_seconds"])
    if "dns_timeout_seconds" in raw:
        dns = _parse_value("dns_timeout_seconds", raw["dns_timeout_seconds"])
    if "smtp_mail_from" in raw and (raw["smtp_mail_from"] or "").strip():
        mail_from = raw["smtp_mail_from"].strip()
    if "enabled_pattern_indices" in raw:
        parsed = _parse_value("enabled_pattern_indices", raw["enabled_pattern_indices"])
        if len(parsed) >= MIN_PATTERNS_ENABLED:
            indices = parsed

    # Búsqueda web
    web_search_provider = raw.get("web_search_provider", "").strip()
    web_search_api_key = raw.get("web_search_api_key", "").strip()
    # Permitir leads sin apellido
    allow_no_lastname = raw.get("allow_no_lastname", "").strip().lower() in ("true", "1", "yes")
    # Patrones personalizados del workspace
    custom_patterns: list[str] = []
    if "custom_patterns" in raw:
        custom_patterns = _parse_value("custom_patterns", raw["custom_patterns"])

    return {
        "smtp_timeout_seconds": smtp,
        "dns_timeout_seconds": dns,
        "enabled_pattern_indices": indices,
        "smtp_mail_from": mail_from,
        "web_search_provider": web_search_provider,
        "web_search_api_key": web_search_api_key,
        "allow_no_lastname": allow_no_lastname,
        "custom_patterns": custom_patterns,
    }


def merge_config_for_response(entries: list[WorkspaceConfigEntry]) -> dict[str, Any]:
    """
    Merge workspace config entries with global defaults for API response.
    Masks sensitive values and includes pattern labels.
    """
    raw = {e.key: e.value for e in entries}
    smtp = getattr(settings, "smtp_timeout_seconds", 5)
    dns = getattr(settings, "dns_timeout_seconds", 5.0)
    mail_from = getattr(settings, "smtp_mail_from", "noreply@mailcheck.local")
    indices = list(range(PATTERN_COUNT))

    if "smtp_timeout_seconds" in raw:
        smtp = max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, int(raw["smtp_timeout_seconds"])))
    if "dns_timeout_seconds" in raw:
        dns = max(MIN_TIMEOUT_SECONDS, min(MAX_TIMEOUT_SECONDS, float(raw["dns_timeout_seconds"])))
    if "smtp_mail_from" in raw and (raw["smtp_mail_from"] or "").strip():
        mail_from = raw["smtp_mail_from"].strip()
    if "enabled_pattern_indices" in raw:
        try:
            parsed = json.loads(raw["enabled_pattern_indices"])
            if isinstance(parsed, list) and len(parsed) >= MIN_PATTERNS_ENABLED:
                indices = [i for i in parsed if isinstance(i, int) and 0 <= i < PATTERN_COUNT][:PATTERN_COUNT]
                if len(indices) < MIN_PATTERNS_ENABLED:
                    indices = list(range(PATTERN_COUNT))
        except (json.JSONDecodeError, TypeError):
            pass

    # Web search settings
    web_search_provider = raw.get("web_search_provider", "").strip()
    web_search_api_key = raw.get("web_search_api_key", "").strip()
    # Mask API key for security
    web_search_api_key_masked = (
        ("*" * 8 + web_search_api_key[-4:]) if len(web_search_api_key) > 4 
        else ("*" * len(web_search_api_key))
    )
    # Allow leads without last name
    allow_no_lastname = raw.get("allow_no_lastname", "").strip().lower() in ("true", "1", "yes")
    # Custom patterns
    custom_patterns: list[str] = []
    if "custom_patterns" in raw:
        custom_patterns = _parse_value("custom_patterns", raw["custom_patterns"])

    return {
        "smtp_timeout_seconds": smtp,
        "dns_timeout_seconds": dns,
        "enabled_pattern_indices": indices,
        "smtp_mail_from": mail_from,
        "web_search_provider": web_search_provider,
        "web_search_api_key": web_search_api_key_masked if web_search_api_key else "",
        "allow_no_lastname": allow_no_lastname,
        "custom_patterns": custom_patterns,
        "pattern_labels": [COMMON_PATTERNS[i] for i in range(PATTERN_COUNT)],
    }
