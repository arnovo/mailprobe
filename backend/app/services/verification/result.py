"""Verification result dataclass and disposable domains list."""
from __future__ import annotations

from dataclasses import dataclass

# Disposable/temporary email domains (subset; extensible without migration)
DISPOSABLE_DOMAINS = frozenset({
    "mailinator.com", "mailinator.net", "guerrillamail.com", "guerrillamail.net",
    "tempmail.com", "temp-mail.org", "10minutemail.com", "throwaway.email",
    "maildrop.cc", "yopmail.com", "getnada.com", "fakeinbox.com", "trashmail.com",
    "sharklasers.com", "guerrillamailblock.com", "mailnesia.com", "dispostable.com",
})


@dataclass
class VerifyResult:
    """Result of email verification."""
    email: str
    status: str  # valid | invalid | risky | unknown
    reason: str
    mx_found: bool
    catch_all: bool
    smtp_check: bool
    confidence_score: int
    smtp_code_msg: str | None = None  # e.g. "250 OK" or "550 User unknown"
    web_mentioned: bool = False  # True if email found in public sources (web search)
