"""Workspace verification config schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

# Limits (must match workspace_config.py)
MAX_TIMEOUT_SECONDS = 30
MIN_TIMEOUT_SECONDS = 1
MIN_PATTERNS_ENABLED = 5
PATTERN_COUNT = 10


MAX_CUSTOM_PATTERNS = 20


class ConfigResponse(BaseModel):
    """Current config (merged with globals)."""

    smtp_timeout_seconds: int = Field(..., ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    dns_timeout_seconds: float = Field(..., ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    enabled_pattern_indices: list[int] = Field(..., min_length=MIN_PATTERNS_ENABLED)
    smtp_mail_from: str = Field(..., min_length=1, max_length=255)
    # Optional web search (bing | serper | empty)
    web_search_provider: str = ""
    web_search_api_key: str = (
        ""  # Note: in response we return only if set or not (for security); or the client knows it
    )
    # Allow leads without last name (generates generic patterns: info@, contact@, etc.)
    allow_no_lastname: bool = False
    # Custom patterns from workspace (additional to standard ones)
    custom_patterns: list[str] = Field(default_factory=list)
    # For frontend: pattern labels (index -> description)
    pattern_labels: list[str] | None = None


class ConfigUpdate(BaseModel):
    """Body for updating config (optional fields; null = use global)."""

    smtp_timeout_seconds: int | None = Field(None, ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    dns_timeout_seconds: float | None = Field(None, ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS)
    enabled_pattern_indices: list[int] | None = Field(
        None,
        min_length=MIN_PATTERNS_ENABLED,
        max_length=PATTERN_COUNT,
    )
    smtp_mail_from: str | None = Field(None, max_length=255)  # "" or null = use global
    web_search_provider: str | None = Field(None, max_length=50)  # "bing" | "serper" | "" (empty = no search)
    web_search_api_key: str | None = Field(None, max_length=255)  # "" or null = delete
    allow_no_lastname: bool | None = None  # Allow leads without last name
    custom_patterns: list[str] | None = Field(None, max_length=MAX_CUSTOM_PATTERNS)  # Custom patterns