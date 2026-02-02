\
from __future__ import annotations
import random
import smtplib
import socket
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List

import dns.resolver

SMTP_TIMEOUT_SECS = 8

@dataclass
class VerifyResult:
    email: str
    status: str              # valid | invalid | risky | unknown
    reason: str
    mx_found: bool
    catch_all: bool
    smtp_check: bool
    confidence_score: int

def mx_lookup(domain: str) -> List[Tuple[int, str]]:
    """
    Returns list of (preference, exchange) sorted by preference.
    """
    answers = dns.resolver.resolve(domain, "MX")
    mx = []
    for r in answers:
        mx.append((int(r.preference), str(r.exchange).rstrip(".")))
    mx.sort(key=lambda x: x[0])
    return mx

def _smtp_probe_rcpt(mx_host: str, candidate_email: str, mail_from: str) -> Tuple[bool, str]:
    """
    Best-effort SMTP RCPT probe. Returns (accepted, detail).
    accepted=True implies server accepted RCPT (not a guarantee of deliverability).
    """
    try:
        with smtplib.SMTP(mx_host, 25, timeout=SMTP_TIMEOUT_SECS) as s:
            s.set_debuglevel(0)
            s.ehlo_or_helo_if_needed()
            # Some servers require STARTTLS; probing with TLS is complex here;
            # We'll keep it simple and handle failures gracefully.
            s.mail(mail_from)
            code, msg = s.rcpt(candidate_email)
            # 250/251 accepted, 450/451/452 temp, 550 etc rejected
            if 200 <= code < 300:
                return True, f"RCPT accepted ({code})"
            if 400 <= code < 500:
                return False, f"Temporary failure ({code})"
            return False, f"Rejected ({code})"
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, smtplib.SMTPHeloError,
            smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError,
            socket.timeout, OSError) as e:
        return False, f"SMTP error: {type(e).__name__}"

def detect_catch_all(mx_hosts: List[str], domain: str, mail_from: str) -> Tuple[bool, bool, str]:
    """
    Returns (catch_all_detected, smtp_attempted, reason)
    """
    # Random local part likely not to exist
    rnd = "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(18))
    test_email = f"{rnd}@{domain}"

    for mx in mx_hosts[:2]:  # keep it light
        accepted, detail = _smtp_probe_rcpt(mx, test_email, mail_from)
        # If accepted for random address, might be catch-all
        if accepted:
            return True, True, f"Random RCPT accepted on {mx}: {detail}"
        # If we couldn't really probe, move on
        if "SMTP error" in detail or "Temporary" in detail:
            continue
        # Rejected random is a good sign of no catch-all on that MX (not definitive)
        return False, True, f"Random RCPT rejected on {mx}: {detail}"
    return False, False, "Could not reliably probe catch-all"

def verify_email(email: str, mail_from: str = "noreply@mailcheck.local") -> VerifyResult:
    """
    Best-effort verification:
    - MX lookup
    - catch-all detection (optional)
    - SMTP RCPT probe (best-effort)
    """
    try:
        local, domain = email.split("@", 1)
    except ValueError:
        return VerifyResult(email, "invalid", "Malformed email", False, False, False, 0)

    domain = domain.strip().lower()
    try:
        mx = mx_lookup(domain)
    except Exception:
        return VerifyResult(email, "invalid", "No MX records (or DNS failed)", False, False, False, 5)

    mx_hosts = [h for _, h in mx]
    mx_found = True

    catch_all, catch_smtp, catch_reason = detect_catch_all(mx_hosts, domain, mail_from)

    # Now probe candidate
    smtp_attempted = False
    accepted_any = False
    detail_any = ""
    for mxh in mx_hosts[:2]:
        accepted, detail = _smtp_probe_rcpt(mxh, email, mail_from)
        smtp_attempted = True
        detail_any = f"{mxh}: {detail}"
        if accepted:
            accepted_any = True
            break
        # If temporary or error, try next
        if "Temporary" in detail or "SMTP error" in detail:
            continue
        # Rejected is strong signal; stop early
        if "Rejected" in detail:
            break

    # Scoring heuristic
    score = 35
    reason_parts = []
    if mx_found:
        score += 20
        reason_parts.append("MX ok")
    if catch_all:
        score -= 10
        reason_parts.append("catch-all possible")
    else:
        reason_parts.append("no catch-all signal" if catch_smtp else "catch-all unknown")

    if smtp_attempted:
        reason_parts.append(f"SMTP: {detail_any}")
    else:
        reason_parts.append("SMTP not attempted")

    if accepted_any and not catch_all:
        score += 35
        status = "valid"
        reason = " | ".join(reason_parts)
    elif accepted_any and catch_all:
        score += 15
        status = "risky"
        reason = " | ".join(reason_parts)
    else:
        # Not accepted could still be unknown if blocked
        if any(k in detail_any for k in ["SMTP error", "Temporary"]):
            status = "unknown"
            score = max(10, score - 5)
        else:
            status = "invalid"
            score = max(5, score - 20)
        reason = " | ".join(reason_parts)

    score = int(max(0, min(100, score)))
    return VerifyResult(
        email=email,
        status=status,
        reason=reason,
        mx_found=mx_found,
        catch_all=catch_all,
        smtp_check=smtp_attempted,
        confidence_score=score,
    )
