"""Main email verification logic: verify_email and verify_and_pick_best."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.services.verification.dns_checker import (
    DNS_TIMEOUT_SECS,
    check_domain_spf_dmarc,
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


def verify_email(
    email: str,
    mail_from: str | None = None,
    smtp_timeout_seconds: int | None = None,
    dns_timeout_seconds: float | None = None,
    detail_callback: Callable[[str], None] | None = None,
) -> VerifyResult:
    """
    Best-effort email verification: format, disposable domain, MX, SPF/DMARC, catch-all, SMTP RCPT.
    """
    mail_from = mail_from or DEFAULT_MAIL_FROM
    
    # Parse email
    try:
        local, domain = email.split("@", 1)
    except ValueError:
        return VerifyResult(email, "invalid", "Malformed email", False, False, False, 0)

    local = (local or "").strip()
    domain = domain.strip().lower()
    
    # Basic format validation
    if not local or not domain or "." not in domain or " " in email:
        return VerifyResult(email, "invalid", "Invalid email format", False, False, False, 0)

    # Check disposable domain
    if domain in DISPOSABLE_DOMAINS:
        if detail_callback:
            detail_callback(f"[Validation] Disposable/temporary domain: {domain}")
        return VerifyResult(email, "invalid", "Disposable or temporary domain", False, False, False, 0)
    
    # MX lookup
    try:
        mx = mx_lookup(domain, dns_timeout_seconds=dns_timeout_seconds)
    except Exception as e:
        if detail_callback:
            detail_callback(f"[MX] Lookup of {domain} failed: {type(e).__name__}: {e}")
        return VerifyResult(email, "invalid", "No MX records (or DNS failed)", False, False, False, 5)

    mx_hosts = [h for _, h in mx]
    mx_found = True
    
    if detail_callback:
        mx_list = ", ".join(f"{pref}={host}" for pref, host in mx)
        detail_callback(f"[MX] Domain {domain}: {len(mx)} MX record(s) -> {mx_list}")

    # Detect catch-all
    catch_all, catch_smtp, catch_reason = detect_catch_all(
        mx_hosts, domain, mail_from,
        smtp_timeout_seconds=smtp_timeout_seconds,
        dns_timeout_seconds=dns_timeout_seconds,
        detail_callback=detail_callback,
    )

    # SMTP RCPT probe
    smtp_attempted = False
    accepted_any = False
    detail_any = ""
    smtp_short: str | None = None
    
    for mxh in mx_hosts[:2]:
        if detail_callback:
            detail_callback(f"[RCPT] Verifying mailbox {email} on MX server: {mxh}")
        
        accepted, detail, short = smtp_probe_rcpt(
            mxh, email, mail_from,
            smtp_timeout_seconds=smtp_timeout_seconds,
            dns_timeout_seconds=dns_timeout_seconds,
            detail_callback=detail_callback,
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

    # Calculate score and determine status
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
        if any(k in detail_any for k in ["SMTP error", "Temporary"]):
            status = "unknown"
            score = max(10, score - 5)
            if "Timeout" in detail_any or "SMTP error" in detail_any:
                reason_parts.append(
                    "Possible mail firewall (Barracuda, etc.): "
                    "the email shown is the most likely candidate but not verified."
                )
            has_spf, has_dmarc = check_domain_spf_dmarc(domain, dns_timeout_seconds=dns_timeout_seconds)
            if detail_callback and (has_spf or has_dmarc):
                detail_callback(f"[Validation] Domain {domain}: SPF={has_spf}, DMARC={has_dmarc}")
            if has_spf or has_dmarc:
                parts = [p for p in ("SPF" if has_spf else None, "DMARC" if has_dmarc else None) if p]
                reason_parts.append(f"Domain with {'/'.join(parts)}; it's common for them not to respond to SMTP probes.")
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
        smtp_code_msg=smtp_short,
    )


def verify_and_pick_best(
    first_name: str,
    last_name: str,
    domain: str,
    mail_from: str | None = None,
    progress_callback: Callable[[str | None, str | None, str | None], None] | None = None,
    detail_callback: Callable[[str], None] | None = None,
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
        progress_callback: Optional; (public_msg, candidate_email, smtp_response)
        detail_callback: Optional; detailed messages for superadmin only
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

    candidates = generate_candidates(
        first_name, last_name, domain,
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
    
    if detail_callback:
        detail_callback(f"[Config] MAIL FROM=<{mail_from}>, timeout SMTP={smtp_to}s, DNS={dns_to}s")
        candidates_preview = ", ".join(candidates[:10])
        suffix = "..." if len(candidates) > 10 else ""
        detail_callback(f"[Config] Domain={domain}, candidates generated={len(candidates)}: {candidates_preview}{suffix}")

    rank = {"valid": 3, "risky": 2, "unknown": 1, "invalid": 0}
    best_email = ""
    best_result: VerifyResult | None = None
    probe_results: dict[str, Any] = {}
    total = len(candidates)

    for i, cand in enumerate(candidates):
        if detail_callback:
            detail_callback(f"--- Candidate {i + 1}/{total}: {cand} ---")
        if progress_callback:
            progress_callback(f"Verifying candidate {i + 1}/{total}...", cand, None)
        
        res = verify_email(
            cand,
            mail_from=mail_from,
            smtp_timeout_seconds=smtp_timeout_seconds,
            dns_timeout_seconds=dns_timeout_seconds,
            detail_callback=detail_callback,
        )
        
        if progress_callback:
            progress_callback(None, None, res.smtp_code_msg or "(no SMTP response)")
        
        probe_results[cand] = {
            "accepted": res.status in ("valid", "risky") and res.mx_found,
            "detail": res.reason,
            "status": res.status,
            "confidence_score": res.confidence_score,
        }
        
        if best_result is None or (res.confidence_score, rank.get(res.status, 0)) > (
            best_result.confidence_score, rank.get(best_result.status, 0)
        ):
            best_result = res
            best_email = cand

    # Optional web search: if best result is unknown (or valid), search if email appears in public sources
    if best_result and best_email:
        if web_search_provider and web_search_api_key:
            if detail_callback:
                detail_callback(f"[Web] Searching if email appears in public sources (provider: {web_search_provider})...")
            
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
                if detail_callback:
                    detail_callback("[Web] Email found in public sources.")
            elif error_msg:
                if detail_callback:
                    detail_callback(f"[Web] Search error: {error_msg}")
            else:
                if detail_callback:
                    detail_callback("[Web] Email not found in public sources.")
        elif detail_callback:
            # Warn that web search was skipped due to missing configuration
            if not web_search_provider:
                detail_callback("[Web] Web search skipped: no provider configured (Dashboard → Configuration).")
            elif not web_search_api_key:
                detail_callback(f"[Web] Web search skipped: provider '{web_search_provider}' configured but no API key.")

    return candidates, best_email or (candidates[0] if candidates else ""), best_result, probe_results
