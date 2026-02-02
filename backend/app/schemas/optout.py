"""Opt-out schemas."""

from __future__ import annotations

from pydantic import BaseModel


class OptOutRequest(BaseModel):
    email: str | None = None
    domain: str | None = None
    lead_id: int | None = None
    reason: str = ""
