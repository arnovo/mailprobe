"""Verify schemas."""
from __future__ import annotations

from pydantic import BaseModel


class VerifyStatelessRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    domain: str = ""


class VerifyCandidate(BaseModel):
    email: str
    status: str
    confidence_score: int
    web_mentioned: bool = False


class VerifyStatelessResponse(BaseModel):
    candidates: list[str]
    best: str | None = None
    best_result: VerifyCandidate | None = None
