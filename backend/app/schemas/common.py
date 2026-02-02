"""Common API response schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response: data, error, and optional meta."""

    data: T | None = None
    error: dict | None = None
    meta: dict | None = None

    @classmethod
    def ok(cls, data: T, meta: dict | None = None) -> APIResponse[T]:
        return cls(data=data, error=None, meta=meta)

    @classmethod
    def err(cls, code: str, message: str, details: dict | None = None) -> APIResponse[None]:
        return cls(data=None, error={"code": code, "message": message, "details": details or {}}, meta=None)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list."""

    items: list[T]
    page: int = 1
    page_size: int = 20
    total: int = 0


class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | running | succeeded | failed | cancelled
    progress: int = 0
    result: dict | None = None
    error: str | None = None
    log_lines: list[str] | None = None  # log paso a paso de la verificación


class JobListItem(BaseModel):
    """Item para listado de jobs (activos o todos)."""

    job_id: str
    kind: str
    status: str
    progress: int = 0
    lead_id: int | None = None
    created_at: str | None = None  # ISO datetime
