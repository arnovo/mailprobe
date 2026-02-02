"""Email verification module."""
from app.services.verification.dns_checker import (
    DNS_TIMEOUT_SECS,
    check_domain_spf_dmarc,
    mx_lookup,
    resolve_to_ip,
)
from app.services.verification.result import DISPOSABLE_DOMAINS, VerifyResult
from app.services.verification.smtp_checker import (
    DEFAULT_MAIL_FROM,
    SMTP_TIMEOUT_SECS,
    detect_catch_all,
    smtp_probe_rcpt,
)
from app.services.verification.verifier import verify_and_pick_best, verify_email
from app.services.verification.web_search import (
    check_email_bing,
    check_email_mentioned_on_web,
    check_email_serper,
)

__all__ = [
    # Result
    "VerifyResult",
    "DISPOSABLE_DOMAINS",
    # DNS
    "mx_lookup",
    "resolve_to_ip",
    "check_domain_spf_dmarc",
    "DNS_TIMEOUT_SECS",
    # SMTP
    "smtp_probe_rcpt",
    "detect_catch_all",
    "SMTP_TIMEOUT_SECS",
    "DEFAULT_MAIL_FROM",
    # Web search
    "check_email_bing",
    "check_email_serper",
    "check_email_mentioned_on_web",
    # Main functions
    "verify_email",
    "verify_and_pick_best",
]
