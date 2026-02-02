"""
Email verification module.

DEPRECATED: This module is kept for backward compatibility.
Import from app.services.verification instead.
"""
from app.services.verification import (
    DEFAULT_MAIL_FROM,
    DISPOSABLE_DOMAINS,
    DNS_TIMEOUT_SECS,
    SMTP_TIMEOUT_SECS,
    VerifyResult,
    check_domain_spf_dmarc,
    check_email_bing,
    check_email_mentioned_on_web,
    check_email_serper,
    detect_catch_all,
    mx_lookup,
    resolve_to_ip,
    smtp_probe_rcpt,
    verify_and_pick_best,
    verify_email,
)

__all__ = [
    "VerifyResult",
    "DISPOSABLE_DOMAINS",
    "mx_lookup",
    "resolve_to_ip",
    "check_domain_spf_dmarc",
    "DNS_TIMEOUT_SECS",
    "smtp_probe_rcpt",
    "detect_catch_all",
    "SMTP_TIMEOUT_SECS",
    "DEFAULT_MAIL_FROM",
    "check_email_bing",
    "check_email_serper",
    "check_email_mentioned_on_web",
    "verify_email",
    "verify_and_pick_best",
]
