"""Internationalization endpoints for error codes and messages."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.error_codes import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    ErrorCode,
    get_all_error_codes,
    get_error_message,
)
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/locales")
async def list_locales() -> APIResponse:
    """List all supported locales.

    Returns:
        List of locale codes with default indicated.
    """
    return APIResponse.ok(
        {
            "locales": SUPPORTED_LOCALES,
            "default": DEFAULT_LOCALE,
        }
    )


@router.get("/error-codes")
async def list_error_codes(
    locale: str = Query(DEFAULT_LOCALE, description="Locale code (en, es)"),
) -> APIResponse:
    """Get all error codes with their localized messages.

    This endpoint is used by the frontend to display localized error messages.
    The frontend should cache this response and use the error code from API
    responses to look up the appropriate message.

    Args:
        locale: Language code (en, es). Defaults to Spanish.

    Returns:
        Dictionary mapping error codes to their localized messages.
    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    codes = get_all_error_codes(locale)
    return APIResponse.ok(
        {
            "locale": locale,
            "codes": codes,
        }
    )


@router.get("/error-codes/{code}")
async def get_error_code(
    code: str,
    locale: str = Query(DEFAULT_LOCALE, description="Locale code (en, es)"),
) -> APIResponse:
    """Get a single error code with its localized message.

    Args:
        code: Error code (e.g., AUTH_INVALID_CREDENTIALS)
        locale: Language code (en, es). Defaults to Spanish.

    Returns:
        Error code details with localized message.
    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    # Validate code exists
    try:
        error_code = ErrorCode(code)
    except ValueError:
        return APIResponse.err(
            ErrorCode.RESOURCE_NOT_FOUND.value,
            f"Error code '{code}' not found",
            {"code": code, "available_codes": [e.value for e in ErrorCode]},
        )

    message = get_error_message(error_code, locale)
    return APIResponse.ok(
        {
            "code": error_code.value,
            "message": message,
            "locale": locale,
        }
    )
