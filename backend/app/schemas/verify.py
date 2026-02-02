"""Verify schemas."""

from __future__ import annotations

from pydantic import BaseModel


class VerifyStatelessRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    domain: str = ""


class VerifyCandidate(BaseModel):
    """Verification result for a single email candidate."""

    email: str
    status: str  # valid | invalid | risky | unknown
    confidence_score: int
    # DNS signals
    mx_found: bool = False
    spf_present: bool = False
    dmarc_present: bool = False
    # SMTP signals
    catch_all: bool | None = None  # None if not attempted
    smtp_attempted: bool = False
    smtp_blocked: bool = False
    # Additional signals
    provider: str = "other"  # google, microsoft, ionos, etc.
    web_mentioned: bool = False
    # Summary
    signals: list[str] = []  # ["mx", "spf", "dmarc", "web", "provider:google"]
    reason: str = ""


class VerifyStatelessResponse(BaseModel):
    candidates: list[str]
    best: str | None = None
    best_result: VerifyCandidate | None = None
