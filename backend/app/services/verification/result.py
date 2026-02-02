"""Verification result dataclass and disposable domains list."""

from __future__ import annotations

from dataclasses import dataclass, field

# Disposable/temporary email domains (subset; extensible without migration)
DISPOSABLE_DOMAINS = frozenset(
    {
        "mailinator.com",
        "mailinator.net",
        "guerrillamail.com",
        "guerrillamail.net",
        "tempmail.com",
        "temp-mail.org",
        "10minutemail.com",
        "throwaway.email",
        "maildrop.cc",
        "yopmail.com",
        "getnada.com",
        "fakeinbox.com",
        "trashmail.com",
        "sharklasers.com",
        "guerrillamailblock.com",
        "mailnesia.com",
        "dispostable.com",
    }
)


@dataclass
class VerifyResult:
    """Result of email verification."""

    email: str
    status: str  # valid | invalid | risky | unknown
    reason: str
    confidence_score: int
    # DNS signals
    mx_found: bool
    spf_present: bool = False
    dmarc_present: bool = False
    # SMTP signals
    catch_all: bool | None = None  # None if not attempted
    smtp_check: bool = False  # deprecated, kept for backward compatibility
    smtp_attempted: bool = False
    smtp_blocked: bool = False
    smtp_code_msg: str | None = None  # e.g. "250 OK" or "550 User unknown"
    # Additional signals
    provider: str = "other"  # google, microsoft, ionos, etc.
    web_mentioned: bool = False  # True if email found in public sources
    pattern_confidence: int | None = None  # 0-100, bonus if domain pattern known
    # Summary
    signals: list[str] = field(default_factory=list)  # ["mx", "spf", "dmarc", "web"]
