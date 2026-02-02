"""Workspace verification config schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

# Límites (deben coincidir con workspace_config.py)
MAX_TIMEOUT_SECONDS = 30
MIN_TIMEOUT_SECONDS = 1
MIN_PATTERNS_ENABLED = 5
PATTERN_COUNT = 10


MAX_CUSTOM_PATTERNS = 20


class ConfigResponse(BaseModel):
    """Config actual (fusionada con globales)."""

    smtp_timeout_seconds: int = Field(..., ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    dns_timeout_seconds: float = Field(..., ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    enabled_pattern_indices: list[int] = Field(..., min_length=MIN_PATTERNS_ENABLED)
    smtp_mail_from: str = Field(..., min_length=1, max_length=255)
    # Búsqueda web opcional (bing | serper | vacío)
    web_search_provider: str = ""
    web_search_api_key: str = (
        ""  # Nota: en respuesta devolvemos solo si hay o no (por seguridad); o el cliente la conoce
    )
    # Permitir leads sin apellido (genera patrones genéricos: info@, contact@, etc.)
    allow_no_lastname: bool = False
    # Patrones personalizados del workspace (adicionales a los estándar)
    custom_patterns: list[str] = Field(default_factory=list)
    # Para el front: etiquetas de patrones (índice -> descripción)
    pattern_labels: list[str] | None = None


class ConfigUpdate(BaseModel):
    """Body para actualizar config (campos opcionales; null = usar global)."""

    smtp_timeout_seconds: int | None = Field(None, ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    dns_timeout_seconds: float | None = Field(None, ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    enabled_pattern_indices: list[int] | None = Field(
        None,
        min_length=MIN_PATTERNS_ENABLED,
        max_length=PATTERN_COUNT,
    )
    smtp_mail_from: str | None = Field(None, max_length=255)  # "" o null = usar global
    web_search_provider: str | None = Field(None, max_length=50)  # "bing" | "serper" | "" (vacío = no buscar)
    web_search_api_key: str | None = Field(None, max_length=255)  # "" o null = borrar
    allow_no_lastname: bool | None = None  # Permitir leads sin apellido
    custom_patterns: list[str] | None = Field(None, max_length=MAX_CUSTOM_PATTERNS)  # Patrones personalizados
