"""Centralized logging service for verification jobs with i18n support.

Usage:
    logger = VerificationLogger(detail_callback)
    logger.mx_lookup(domain="example.com", count=3, hosts="mx1, mx2, mx3")
"""

from __future__ import annotations

import json
from collections.abc import Callable

from app.core.log_constants import LogCode, LogParam


def make_log_message(code: LogCode | str, params: dict | None = None) -> str:
    """Create a JSON log message with code and params for i18n translation."""
    data = {"code": code if isinstance(code, str) else code.value}
    if params:
        # Convert LogParam enum keys to strings
        data["params"] = {(k.value if isinstance(k, LogParam) else k): v for k, v in params.items()}
    return json.dumps(data, ensure_ascii=False)


def parse_log_message(message: str) -> tuple[str | None, dict]:
    """Parse a log message. Returns (code, params) if JSON with code, else (None, {})."""
    try:
        data = json.loads(message)
        if isinstance(data, dict) and "code" in data:
            return data["code"], data.get("params", {})
    except (json.JSONDecodeError, TypeError):
        pass
    return None, {}


class VerificationLogger:
    """Centralized logger for verification jobs with i18n support.

    All methods are type-safe and use LogCode/LogParam enums to avoid magic strings.
    Messages are serialized as JSON for frontend translation.
    """

    def __init__(
        self,
        detail_callback: Callable[[str], None] | None = None,
        progress_callback: Callable[[str | None, str | None, str | None], None] | None = None,
    ):
        self._detail = detail_callback
        self._progress = progress_callback

    def _emit(self, code: LogCode, params: dict | None = None) -> None:
        """Emit a log message to detail callback."""
        if self._detail:
            self._detail(make_log_message(code, params))

    def _emit_progress(self, code: LogCode, params: dict | None = None, email: str | None = None) -> None:
        """Emit a progress message to progress callback."""
        if self._progress:
            self._progress(make_log_message(code, params), email, None)

    # =========================================================================
    # Job lifecycle
    # =========================================================================

    def job_started(self, job_type: str, lead_id: int, workspace_id: int) -> None:
        self._emit(
            LogCode.JOB_STARTED,
            {
                LogParam.JOB_TYPE: job_type,
                LogParam.LEAD_ID: lead_id,
                LogParam.WORKSPACE_ID: workspace_id,
            },
        )

    def job_starting_verification(self) -> None:
        self._emit(LogCode.JOB_STARTING_VERIFICATION)

    def job_completed(self, lead_id: int) -> None:
        self._emit(LogCode.JOB_COMPLETED, {LogParam.LEAD_ID: lead_id})

    def job_failed(self, reason: str) -> None:
        self._emit(LogCode.JOB_FAILED, {LogParam.REASON: reason})

    def job_timeout(self) -> None:
        self._emit(LogCode.JOB_TIMEOUT)

    # =========================================================================
    # Verification steps (public)
    # =========================================================================

    def verify_domain(self, domain: str) -> None:
        self._emit(LogCode.VERIFY_DOMAIN, {LogParam.DOMAIN: domain})
        self._emit_progress(LogCode.VERIFY_DOMAIN, {LogParam.DOMAIN: domain})

    def verify_generating_candidates(self) -> None:
        self._emit(LogCode.VERIFY_GENERATING_CANDIDATES)
        self._emit_progress(LogCode.VERIFY_GENERATING_CANDIDATES)

    def verify_checking_mail_server(self) -> None:
        self._emit(LogCode.VERIFY_CHECKING_MAIL_SERVER)
        self._emit_progress(LogCode.VERIFY_CHECKING_MAIL_SERVER)

    def verify_candidate(self, index: int, total: int, email: str) -> None:
        self._emit_progress(
            LogCode.VERIFY_CANDIDATE,
            {LogParam.INDEX: index, LogParam.TOTAL: total},
            email,
        )

    def verify_completed(self, email: str) -> None:
        self._emit(LogCode.VERIFY_COMPLETED, {LogParam.EMAIL: email})

    def verify_no_email_found(self) -> None:
        self._emit(LogCode.VERIFY_NO_EMAIL_FOUND)

    # =========================================================================
    # Debug: Worker/Lead
    # =========================================================================

    def debug_worker_processing(self, job_id: str, lead_id: int, workspace_id: int) -> None:
        self._emit(
            LogCode.DEBUG_WORKER_PROCESSING,
            {
                LogParam.JOB_ID: job_id,
                LogParam.LEAD_ID: lead_id,
                LogParam.WORKSPACE_ID: workspace_id,
            },
        )

    def debug_lead_loaded(self, lead_id: int, domain: str, first_name: str, last_name: str) -> None:
        self._emit(
            LogCode.DEBUG_LEAD_LOADED,
            {
                LogParam.LEAD_ID: lead_id,
                LogParam.DOMAIN: domain,
                LogParam.FIRST_NAME: first_name,
                LogParam.LAST_NAME: last_name,
            },
        )

    def debug_calling_verifier(self, first_name: str, last_name: str, domain: str) -> None:
        self._emit(
            LogCode.DEBUG_CALLING_VERIFIER,
            {
                LogParam.FIRST_NAME: first_name,
                LogParam.LAST_NAME: last_name,
                LogParam.DOMAIN: domain,
            },
        )

    def debug_verifier_result(self, email: str | None, status: str, confidence: int, reason: str) -> None:
        self._emit(
            LogCode.DEBUG_VERIFIER_RESULT,
            {
                LogParam.EMAIL: email or "",
                LogParam.STATUS: status,
                LogParam.CONFIDENCE: confidence,
                LogParam.REASON: reason,
            },
        )

    def debug_config(self, mail_from: str, smtp_timeout: int, dns_timeout: float) -> None:
        self._emit(
            LogCode.DEBUG_CONFIG,
            {
                LogParam.MAIL_FROM: mail_from,
                LogParam.SMTP_TIMEOUT: smtp_timeout,
                LogParam.DNS_TIMEOUT: dns_timeout,
            },
        )

    def debug_candidates_generated(self, domain: str, count: int, preview: str) -> None:
        self._emit(
            LogCode.DEBUG_CANDIDATES_GENERATED,
            {
                LogParam.DOMAIN: domain,
                LogParam.COUNT: count,
                LogParam.PREVIEW: preview,
            },
        )

    def debug_candidate_header(self, index: int, total: int, email: str) -> None:
        self._emit(
            LogCode.DEBUG_CANDIDATE_HEADER,
            {
                LogParam.INDEX: index,
                LogParam.TOTAL: total,
                LogParam.EMAIL: email,
            },
        )

    def debug_candidate_email(self, email: str) -> None:
        self._emit(LogCode.DEBUG_CANDIDATE_EMAIL, {LogParam.EMAIL: email})

    def debug_more_candidates(self, count: int) -> None:
        self._emit(LogCode.DEBUG_MORE_CANDIDATES, {LogParam.COUNT: count})

    # =========================================================================
    # Debug: MX/DNS
    # =========================================================================

    def debug_mx_lookup(self, domain: str, count: int, hosts: str) -> None:
        self._emit(
            LogCode.DEBUG_MX_LOOKUP,
            {
                LogParam.DOMAIN: domain,
                LogParam.COUNT: count,
                LogParam.HOSTS: hosts,
            },
        )

    def debug_mx_lookup_failed(self, domain: str, error_type: str, error: str) -> None:
        self._emit(
            LogCode.DEBUG_MX_LOOKUP_FAILED,
            {
                LogParam.DOMAIN: domain,
                LogParam.ERROR_TYPE: error_type,
                LogParam.ERROR: error,
            },
        )

    def debug_provider_detected(self, provider: str) -> None:
        self._emit(LogCode.DEBUG_PROVIDER_DETECTED, {LogParam.PROVIDER: provider})

    def debug_dns_spf_dmarc(self, spf: bool, dmarc: bool) -> None:
        self._emit(LogCode.DEBUG_DNS_SPF_DMARC, {LogParam.SPF: spf, LogParam.DMARC: dmarc})

    def debug_disposable_domain(self, domain: str) -> None:
        self._emit(LogCode.DEBUG_DISPOSABLE_DOMAIN, {LogParam.DOMAIN: domain})

    # =========================================================================
    # Debug: SMTP
    # =========================================================================

    def debug_smtp_skipped(self) -> None:
        self._emit(LogCode.DEBUG_SMTP_SKIPPED)

    def debug_smtp_dns_resolve(self, host: str, ip: str | None) -> None:
        self._emit(
            LogCode.DEBUG_SMTP_DNS_RESOLVE,
            {
                LogParam.MX_HOST: host,
                LogParam.IP: ip or "failed",
            },
        )

    def debug_smtp_connecting(self, host: str, ip: str, timeout: int) -> None:
        self._emit(
            LogCode.DEBUG_SMTP_CONNECTING,
            {
                LogParam.MX_HOST: host,
                LogParam.IP: ip,
                LogParam.TIMEOUT: timeout,
            },
        )

    def debug_smtp_rcpt_result(self, mail_from: str, email: str, response: str) -> None:
        self._emit(
            LogCode.DEBUG_SMTP_RCPT_RESULT,
            {
                LogParam.MAIL_FROM: mail_from,
                LogParam.EMAIL: email,
                LogParam.RESPONSE: response,
            },
        )

    def debug_smtp_exception(self, host: str, error: str) -> None:
        self._emit(LogCode.DEBUG_SMTP_EXCEPTION, {LogParam.MX_HOST: host, LogParam.ERROR: error})

    def debug_rcpt_verifying(self, email: str, mx_host: str) -> None:
        self._emit(LogCode.DEBUG_RCPT_VERIFYING, {LogParam.EMAIL: email, LogParam.MX_HOST: mx_host})

    # =========================================================================
    # Debug: Catch-all
    # =========================================================================

    def debug_catchall_checking(self, test_email: str) -> None:
        self._emit(LogCode.DEBUG_CATCHALL_CHECKING, {LogParam.TEST_EMAIL: test_email})

    def debug_catchall_testing(self, mx_host: str) -> None:
        self._emit(LogCode.DEBUG_CATCHALL_TESTING, {LogParam.MX_HOST: mx_host})

    def debug_catchall_result(self, mx_host: str, accepted: bool, detail: str) -> None:
        self._emit(
            LogCode.DEBUG_CATCHALL_RESULT,
            {
                LogParam.MX_HOST: mx_host,
                LogParam.ACCEPTED: accepted,
                LogParam.DETAIL: detail,
            },
        )

    def debug_catchall_inconclusive(self) -> None:
        self._emit(LogCode.DEBUG_CATCHALL_INCONCLUSIVE)

    # =========================================================================
    # Debug: Web search
    # =========================================================================

    def debug_web_searching(self, provider: str) -> None:
        self._emit(LogCode.DEBUG_WEB_SEARCHING, {LogParam.PROVIDER: provider})

    def debug_web_found(self) -> None:
        self._emit(LogCode.DEBUG_WEB_FOUND)

    def debug_web_not_found(self) -> None:
        self._emit(LogCode.DEBUG_WEB_NOT_FOUND)

    def debug_web_error(self, error: str) -> None:
        self._emit(LogCode.DEBUG_WEB_ERROR, {LogParam.ERROR: error})

    def debug_web_skipped_no_provider(self) -> None:
        self._emit(LogCode.DEBUG_WEB_SKIPPED_NO_PROVIDER)

    def debug_web_skipped_no_key(self, provider: str) -> None:
        self._emit(LogCode.DEBUG_WEB_SKIPPED_NO_KEY, {LogParam.PROVIDER: provider})

    # =========================================================================
    # Errors
    # =========================================================================

    def error_lead_not_found(self, lead_id: int) -> None:
        self._emit(LogCode.ERROR_LEAD_NOT_FOUND, {LogParam.LEAD_ID: lead_id})

    def error_lead_opted_out(self, lead_id: int) -> None:
        self._emit(LogCode.ERROR_LEAD_OPTED_OUT, {LogParam.LEAD_ID: lead_id})

    def error_generic(self, error: str) -> None:
        self._emit(LogCode.ERROR_GENERIC, {LogParam.ERROR: error})
