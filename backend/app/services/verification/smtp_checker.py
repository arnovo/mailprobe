"""SMTP operations: RCPT probe and catch-all detection."""
from __future__ import annotations

import random
import smtplib
from collections.abc import Callable

from app.core.config import settings
from app.services.smtp_blocked_detector import record_smtp_timeout
from app.services.verification.dns_checker import resolve_to_ip

SMTP_TIMEOUT_SECS = getattr(settings, "smtp_timeout_seconds", 5)
DEFAULT_MAIL_FROM = getattr(settings, "smtp_mail_from", "noreply@mailcheck.local")


def smtp_probe_rcpt(
    mx_host: str,
    candidate_email: str,
    mail_from: str,
    smtp_timeout_seconds: int | None = None,
    dns_timeout_seconds: float | None = None,
    detail_callback: Callable[[str], None] | None = None,
) -> tuple[bool, str, str | None]:
    """
    Best-effort SMTP RCPT probe.
    
    Returns:
        (accepted, detail, short_code_msg)
        - accepted: True if RCPT was accepted (2xx response)
        - detail: Human-readable detail string
        - short_code_msg: e.g. "250 OK" for logging
    """
    smtp_to = smtp_timeout_seconds if smtp_timeout_seconds is not None else SMTP_TIMEOUT_SECS
    ip = resolve_to_ip(mx_host, dns_timeout_seconds=dns_timeout_seconds)
    
    if detail_callback:
        detail_callback(f"  [SMTP] DNS resolution of {mx_host} -> IP: {ip or 'failed (timeout/no A/AAAA)'}")
    
    if not ip:
        return False, "SMTP error: DNS timeout or no A/AAAA", None

    try:
        if detail_callback:
            detail_callback(f"  [SMTP] Connecting to {mx_host} ({ip}:25), timeout={smtp_to}s")
        
        with smtplib.SMTP(ip, 25, timeout=smtp_to) as s:
            s.set_debuglevel(0)
            s.ehlo_or_helo_if_needed()
            s.mail(mail_from)
            code, msg = s.rcpt(candidate_email)
            short = f"{code} {str(msg).strip()}" if msg else str(code)
            
            if detail_callback:
                detail_callback(f"  [SMTP] MAIL FROM:<{mail_from}> RCPT TO:<{candidate_email}> -> {short}")
            
            if 200 <= code < 300:
                return True, f"RCPT accepted ({code})", short
            if 400 <= code < 500:
                return False, f"Temporary failure ({code})", short
            return False, f"Rejected ({code})", short
    
    except smtplib.SMTPConnectError as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        return False, err, None
    except smtplib.SMTPServerDisconnected as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        return False, err, None
    except smtplib.SMTPHeloError as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        return False, err, None
    except smtplib.SMTPRecipientsRefused as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        return False, err, None
    except smtplib.SMTPSenderRefused as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        return False, err, None
    except smtplib.SMTPDataError as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        return False, err, None
    except TimeoutError as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        # Record timeout for SMTP blocked detection
        record_smtp_timeout(mx_host)
        return False, err, None
    except OSError as e:
        err = f"SMTP error: {type(e).__name__}"
        if detail_callback:
            detail_callback(f"  [SMTP] Exception on {mx_host}: {err}")
        # Record timeout for connection-related errors (port blocked, network unreachable)
        if "timed out" in str(e).lower() or "connection refused" in str(e).lower():
            record_smtp_timeout(mx_host)
        return False, err, None


def detect_catch_all(
    mx_hosts: list[str],
    domain: str,
    mail_from: str,
    smtp_timeout_seconds: int | None = None,
    dns_timeout_seconds: float | None = None,
    detail_callback: Callable[[str], None] | None = None,
) -> tuple[bool, bool, str]:
    """
    Detect if domain is a catch-all (accepts any mailbox).
    
    Returns:
        (catch_all_detected, smtp_attempted, reason)
    """
    rnd = "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(18))
    test_email = f"{rnd}@{domain}"
    
    if detail_callback:
        detail_callback(f"[Catch-all] Checking if domain accepts any mailbox: test address {test_email}")

    for mx in mx_hosts[:2]:
        if detail_callback:
            detail_callback(f"[Catch-all] Testing MX server: {mx}")
        
        accepted, detail, short = smtp_probe_rcpt(
            mx, test_email, mail_from,
            smtp_timeout_seconds=smtp_timeout_seconds,
            dns_timeout_seconds=dns_timeout_seconds,
            detail_callback=detail_callback,
        )
        
        if detail_callback:
            detail_callback(f"[Catch-all] Result on {mx}: accepted={accepted}, detail={short or detail}")
        
        if accepted:
            return True, True, f"Random RCPT accepted on {mx}: {detail}"
        if "SMTP error" in detail or "Temporary" in detail:
            continue
        return False, True, f"Random RCPT rejected on {mx}: {detail}"
    
    if detail_callback:
        detail_callback("[Catch-all] Could not reliably test (timeouts/errors on all MX)")
    
    return False, False, "Could not reliably probe catch-all"
