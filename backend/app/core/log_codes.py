"""Log codes for i18n support in job logs.

Log messages are stored as JSON with code + params, translated in frontend.
Format: {"code": "LOG_CODE", "params": {"key": "value"}}
"""
from __future__ import annotations

import json
from enum import Enum


class LogCode(str, Enum):
    """Log codes for verification jobs."""

    # Job lifecycle
    JOB_STARTED = "JOB_STARTED"
    JOB_STARTING_VERIFICATION = "JOB_STARTING_VERIFICATION"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
    JOB_TIMEOUT = "JOB_TIMEOUT"

    # Verification steps
    VERIFY_DOMAIN = "VERIFY_DOMAIN"
    VERIFY_GENERATING_CANDIDATES = "VERIFY_GENERATING_CANDIDATES"
    VERIFY_CHECKING_MAIL_SERVER = "VERIFY_CHECKING_MAIL_SERVER"
    VERIFY_MX_RECORDS = "VERIFY_MX_RECORDS"
    VERIFY_MX_NOT_FOUND = "VERIFY_MX_NOT_FOUND"
    VERIFY_COMPLETED = "VERIFY_COMPLETED"
    VERIFY_NO_EMAIL_FOUND = "VERIFY_NO_EMAIL_FOUND"

    # Errors
    ERROR_LEAD_NOT_FOUND = "ERROR_LEAD_NOT_FOUND"
    ERROR_LEAD_OPTED_OUT = "ERROR_LEAD_OPTED_OUT"
    ERROR_GENERIC = "ERROR_GENERIC"

    # Debug (superadmin only)
    DEBUG_WORKER_PROCESSING = "DEBUG_WORKER_PROCESSING"
    DEBUG_LEAD_LOADED = "DEBUG_LEAD_LOADED"
    DEBUG_CALLING_VERIFIER = "DEBUG_CALLING_VERIFIER"
    DEBUG_VERIFIER_RESULT = "DEBUG_VERIFIER_RESULT"
    DEBUG_MX_LOOKUP = "DEBUG_MX_LOOKUP"
    DEBUG_MX_EXCEPTION = "DEBUG_MX_EXCEPTION"
    DEBUG_CANDIDATE_STATUS = "DEBUG_CANDIDATE_STATUS"
    DEBUG_MORE_CANDIDATES = "DEBUG_MORE_CANDIDATES"


def make_log_message(code: LogCode | str, params: dict | None = None) -> str:
    """Create a JSON log message with code and params for i18n translation."""
    data = {"code": code if isinstance(code, str) else code.value}
    if params:
        data["params"] = params
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
