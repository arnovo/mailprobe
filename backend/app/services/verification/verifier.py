"""Main email verification logic: verify_email and verify_and_pick_best."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.log_service import VerificationLogger
from app.services.smtp_blocked_detector import is_smtp_blocked
from app.services.verification.dns_checker import (
    DNS_TIMEOUT_SECS,
    check_domain_spf_dmarc,
    detect_provider,
    mx_lookup,
)
from app.services.verification.result import DISPOSABLE_DOMAINS, VerifyResult
from app.services.verification.smtp_checker import (
    DEFAULT_MAIL_FROM,
    SMTP_TIMEOUT_SECS,
    detect_catch_all,
    smtp_probe_rcpt,
)
from app.services.verification.web_search import check_email_mentioned_on_web

CANDIDATES_PREVIEW_LIMIT = 10


def verify_email(
    email: str,
    mail_from: str | None = None,
    smtp_timeout_seconds: int | None = None,
    dns_timeout_seconds: float | None = None,
    logger: VerificationLogger | None = None,
) -> VerifyResult:
    """
    Best-effort email verification: format, disposable domain, MX, SPF/DMARC, catch-all, SMTP RCPT.

    When SMTP port 25 is blocked at infrastructure level, uses alternative signals
    (DNS, provider detection, SPF/DMARC) to provide useful results instead of "unknown".
    """
    mail_from = mail_from or DEFAULT_MAIL_FROM
    log = logger or VerificationLogger()

    # Check if SMTP is blocked at infrastructure level
    smtp_blocked = is_smtp_blocked()

    # Parse email
    try:
        local, domain = email.split("@", 1)
    except ValueError:
        return VerifyResult(
            email=email,
            status="invalid",
            reason="Malformed email",
            confidence_score=0,
            mx_found=False,
            smtp_blocked=smtp_blocked,
        )

    local = (local or "").strip()
    domain = domain.strip().lower()

    # Basic format validation
    if not local or not domain or "." not in domain or " " in email:
        return VerifyResult(
            email=email,
            status="invalid",
            reason="Invalid email format",
            confidence_score=0,
            mx_found=False,
            smtp_blocked=smtp_blocked,
        )

    # Check disposable domain
    if domain in DISPOSABLE_DOMAINS:
        log.debug_disposable_domain(domain)
        return VerifyResult(
            email=email,
            status="invalid",
            reason="Disposable or temporary domain",
            confidence_score=0,
            mx_found=False,
            smtp_blocked=smtp_blocked,
        )

    # MX lookup
    try:
        mx = mx_lookup(domain, dns_timeout_seconds=dns_timeout_seconds)
    except Exception as e:
        log.debug_mx_lookup_failed(domain, type(e).__name__, str(e))
        return VerifyResult(
            email=email,
            status="invalid",
            reason="No MX records (or DNS failed)",
            confidence_score=5,
            mx_found=False,
            smtp_blocked=smtp_blocked,
        )

    mx_hosts = [h for _, h in mx]
    mx_found = True

    mx_list = ", ".join(f"{pref}={host}" for pref, host in mx)
    log.debug_mx_lookup(domain, len(mx), mx_list)

    # Detect provider from MX
    provider = detect_provider(mx)
    if provider != "other":
        log.debug_provider_detected(provider)

    # Check SPF/DMARC (always, for scoring)
    spf_present, dmarc_present = check_domain_spf_dmarc(domain, dns_timeout_seconds=dns_timeout_seconds)
    log.debug_dns_spf_dmarc(spf_present, dmarc_present)

    # Initialize SMTP-related variables
    catch_all: bool | None = None
    smtp_attempted = False
    accepted_any = False
    detail_any = ""
    smtp_short: str | None = None

    # Skip SMTP probes if blocked at infrastructure level
    if smtp_blocked:
        log.debug_smtp_skipped()
    else:
        # Detect catch-all
        catch_all_result, catch_smtp, catch_reason = detect_catch_all(
            mx_hosts,
            domain,
            mail_from,
            smtp_timeout_seconds=smtp_timeout_seconds,
            dns_timeout_seconds=dns_timeout_seconds,
            logger=log,
        )
        catch_all = catch_all_result if catch_smtp else None

        # SMTP RCPT probe
        for mxh in mx_hosts[:2]:
            log.debug_rcpt_verifying(email, mxh)

            accepted, detail, short = smtp_probe_rcpt(
                mxh,
                email,
                mail_from,
                smtp_timeout_seconds=smtp_timeout_seconds,
                dns_timeout_seconds=dns_timeout_seconds,
                logger=log,
            )
            smtp_attempted = True
            detail_any = f"{mxh}: {detail}"

            if short is not None:
                smtp_short = short

            if accepted:
                accepted_any = True
                break

            if "Temporary" in detail or "SMTP error" in detail:
                continue
            if "Rejected" in detail:
                break

    # Build signals list
    signals: list[str] = []
    if mx_found:
        signals.append("mx")
    if spf_present:
        signals.append("spf")
    if dmarc_present:
        signals.append("dmarc")
    if provider != "other":
        signals.append(f"provider:{provider}")
    if smtp_blocked:
        signals.append("smtp_blocked")

    # Calculate score and determine status using new signal-based scoring
    score, status, reason = _calculate_score_and_status(
        mx_found=mx_found,
        spf_present=spf_present,
        dmarc_present=dmarc_present,
        provider=provider,
        smtp_blocked=smtp_blocked,
        smtp_attempted=smtp_attempted,
        accepted_any=accepted_any,
        catch_all=catch_all,
        detail_any=detail_any,
    )

    return VerifyResult(
        email=email,
        status=status,
        reason=reason,
        confidence_score=score,
        mx_found=mx_found,
        spf_present=spf_present,
        dmarc_present=dmarc_present,
        catch_all=catch_all,
        smtp_check=smtp_attempted,  # deprecated, kept for compatibility
        smtp_attempted=smtp_attempted,
        smtp_blocked=smtp_blocked,
        smtp_code_msg=smtp_short,
        provider=provider,
        signals=signals,
    )


def _calculate_score_and_status(
    *,
    mx_found: bool,
    spf_present: bool,
    dmarc_present: bool,
    provider: str,
    smtp_blocked: bool,
    smtp_attempted: bool,
    accepted_any: bool,
    catch_all: bool | None,
    detail_any: str,
) -> tuple[int, str, str]:
    """
    Calculate confidence score and status based on available signals.

    Scoring without SMTP:
    - mx_found: +20
    - spf_present: +10
    - dmarc_present: +10
    - known provider (google/microsoft): +10
    - SMTP accepted (if available): +25
    - catch_all detected: -10
    - SMTP rejected 5xx: -30 (invalid)

    Status rules:
    - invalid: bad format, disposable, no MX, SMTP 5xx clear
    - valid: SMTP accepted + no catch-all (only if SMTP available)
    - risky: MX ok + positive signals, no SMTP confirmation
    - unknown: SMTP available but inconclusive (real greylist)
    """
    base_score = 35
    score = base_score
    reason_parts: list[str] = []

    # DNS signals (always available)
    if mx_found:
        score += 20
        reason_parts.append("MX ok")

    if spf_present:
        score += 10
        reason_parts.append("SPF")

    if dmarc_present:
        score += 10
        reason_parts.append("DMARC")

    # Provider bonus
    if provider in ("google", "microsoft", "icloud", "zoho"):
        score += 10
        reason_parts.append(f"provider:{provider}")

    # SMTP-based scoring
    if smtp_blocked:
        # SMTP blocked: use alternative signals, don't penalize
        reason_parts.append("SMTP blocked")

        # With good signals but no SMTP, status is "risky" (not "unknown")
        if mx_found and (spf_present or dmarc_present or provider != "other"):
            status = "risky"
            reason = " | ".join(reason_parts)
        elif mx_found:
            status = "risky"
            score = max(score, 50)  # At least 50 if MX found
            reason = " | ".join(reason_parts)
        else:
            status = "unknown"
            reason = " | ".join(reason_parts)
    elif smtp_attempted:
        # SMTP was attempted
        if catch_all is not None:
            if catch_all:
                score -= 10
                reason_parts.append("catch-all")
            else:
                reason_parts.append("no catch-all")

        if accepted_any and not catch_all:
            score += 25
            status = "valid"
            reason_parts.append(f"SMTP: {detail_any}")
            reason = " | ".join(reason_parts)
        elif accepted_any and catch_all:
            score += 10
            status = "risky"
            reason_parts.append(f"SMTP: {detail_any}")
            reason = " | ".join(reason_parts)
        elif any(k in detail_any for k in ["SMTP error", "Temporary", "Timeout"]):
            # Temporary errors or timeouts
            status = "unknown"
            reason_parts.append(f"SMTP: {detail_any}")
            reason = " | ".join(reason_parts)
        else:
            # Hard rejection (5xx)
            score = max(5, score - 30)
            status = "invalid"
            reason_parts.append(f"SMTP rejected: {detail_any}")
            reason = " | ".join(reason_parts)
    else:
        # SMTP not attempted (but not blocked)
        reason_parts.append("SMTP not attempted")
        status = "risky" if mx_found else "unknown"
        reason = " | ".join(reason_parts)

    score = int(max(0, min(100, score)))
    return score, status, reason


def verify_and_pick_best(
    first_name: str,
    last_name: str,
    domain: str,
    mail_from: str | None = None,
    logger: VerificationLogger | None = None,
    smtp_timeout_seconds: int | None = None,
    dns_timeout_seconds: float | None = None,
    enabled_pattern_indices: list[int] | None = None,
    web_search_provider: str | None = None,
    web_search_api_key: str | None = None,
    allow_no_lastname: bool = False,
    on_web_search_performed: Callable[[str], None] | None = None,
    custom_patterns: list[str] | None = None,
) -> tuple[list[str], str | None, VerifyResult | None, dict[str, Any]]:
    """
    Generate candidates, verify each, return (candidates, best_email, best_result, probe_results_dict).

    Args:
        first_name: Lead's first name
        last_name: Lead's last name
        domain: Email domain
        mail_from: MAIL FROM address for SMTP probes
        logger: VerificationLogger for i18n logs
        smtp_timeout_seconds: SMTP timeout (uses global if not set)
        dns_timeout_seconds: DNS timeout (uses global if not set)
        enabled_pattern_indices: Pattern indices to use (None = all)
        web_search_provider: 'bing' | 'serper' | None
        web_search_api_key: Provider API key
        allow_no_lastname: If True, generate candidates even without last name
        on_web_search_performed: Callback when web search is performed (for usage tracking)
        custom_patterns: Additional patterns defined by the workspace

    Returns:
        (candidates, best_email, best_result, probe_results_dict)
    """
    from app.services.email_patterns import generate_candidates

    log = logger or VerificationLogger()

    candidates = generate_candidates(
        first_name,
        last_name,
        domain,
        max_candidates=15,
        enabled_pattern_indices=enabled_pattern_indices,
        allow_no_lastname=allow_no_lastname,
        custom_patterns=custom_patterns,
    )

    if not candidates:
        return [], "", None, {}

    mail_from = mail_from or DEFAULT_MAIL_FROM
    smtp_to = smtp_timeout_seconds if smtp_timeout_seconds is not None else SMTP_TIMEOUT_SECS
    dns_to = dns_timeout_seconds if dns_timeout_seconds is not None else DNS_TIMEOUT_SECS

    log.debug_config(mail_from, smtp_to, dns_to)
    candidates_preview = ", ".join(candidates[:CANDIDATES_PREVIEW_LIMIT])
    suffix = "..." if len(candidates) > CANDIDATES_PREVIEW_LIMIT else ""
    log.debug_candidates_generated(domain, len(candidates), candidates_preview + suffix)

    rank = {"valid": 3, "risky": 2, "unknown": 1, "invalid": 0}
    best_email = ""
    best_result: VerifyResult | None = None
    probe_results: dict[str, Any] = {}
    total = len(candidates)

    for i, cand in enumerate(candidates):
        log.debug_candidate_header(i + 1, total, cand)
        log.verify_candidate(i + 1, total, cand)

        res = verify_email(
            cand,
            mail_from=mail_from,
            smtp_timeout_seconds=smtp_timeout_seconds,
            dns_timeout_seconds=dns_timeout_seconds,
            logger=log,
        )

        probe_results[cand] = {
            "accepted": res.status in ("valid", "risky") and res.mx_found,
            "detail": res.reason,
            "status": res.status,
            "confidence_score": res.confidence_score,
        }

        if best_result is None or (res.confidence_score, rank.get(res.status, 0)) > (
            best_result.confidence_score,
            rank.get(best_result.status, 0),
        ):
            best_result = res
            best_email = cand

    # Optional web search: if best result is unknown (or valid), search if email appears in public sources
    if best_result and best_email:
        if web_search_provider and web_search_api_key:
            log.debug_web_searching(web_search_provider)

            found, error_msg = check_email_mentioned_on_web(
                best_email,
                provider=web_search_provider,
                api_key=web_search_api_key,
            )

            # Notify that web search was performed (for usage tracking)
            if on_web_search_performed:
                on_web_search_performed(web_search_provider)

            if found:
                best_result.web_mentioned = True
                best_result.reason = (best_result.reason or "").rstrip() + " | Email found in public sources."
                log.debug_web_found()
            elif error_msg:
                log.debug_web_error(error_msg)
            else:
                log.debug_web_not_found()
        else:
            # Warn that web search was skipped due to missing configuration
            if not web_search_provider:
                log.debug_web_skipped_no_provider()
            elif not web_search_api_key:
                log.debug_web_skipped_no_key(web_search_provider)

    return candidates, best_email or (candidates[0] if candidates else ""), best_result, probe_results
