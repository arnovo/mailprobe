"""Standardized error codes with i18n support.

Error codes are returned in API responses. The frontend uses these codes
to display localized error messages to users.

Usage:
    from app.core.error_codes import ErrorCode
    return APIResponse.err(ErrorCode.NOT_FOUND, get_error_message(ErrorCode.NOT_FOUND, "en"))
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""

    # Authentication errors (AUTH_*)
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_USER_DISABLED = "AUTH_USER_DISABLED"
    AUTH_USER_NOT_FOUND = "AUTH_USER_NOT_FOUND"
    AUTH_EMAIL_EXISTS = "AUTH_EMAIL_EXISTS"
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"

    # Validation errors (VALIDATION_*)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VALIDATION_REQUIRED_FIELD = "VALIDATION_REQUIRED_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_MIN_PATTERNS = "VALIDATION_MIN_PATTERNS"
    VALIDATION_INVALID_PROVIDER = "VALIDATION_INVALID_PROVIDER"

    # Resource errors (RESOURCE_*)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Lead-specific errors (LEAD_*)
    LEAD_NOT_FOUND = "LEAD_NOT_FOUND"
    LEAD_OPT_OUT = "LEAD_OPT_OUT"
    LEAD_NO_VERIFICATION_LOG = "LEAD_NO_VERIFICATION_LOG"

    # Job-specific errors (JOB_*)
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_INVALID_STATE = "JOB_INVALID_STATE"
    JOB_TIMEOUT = "JOB_TIMEOUT"

    # Quota/limits errors (QUOTA_*)
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    QUOTA_API_KEYS_LIMIT = "QUOTA_API_KEYS_LIMIT"
    QUOTA_VERIFICATIONS_LIMIT = "QUOTA_VERIFICATIONS_LIMIT"

    # Verification errors (VERIFY_*)
    VERIFY_INVALID_EMAIL = "VERIFY_INVALID_EMAIL"
    VERIFY_DOMAIN_NOT_FOUND = "VERIFY_DOMAIN_NOT_FOUND"
    VERIFY_SMTP_BLOCKED = "VERIFY_SMTP_BLOCKED"
    VERIFY_TIMEOUT = "VERIFY_TIMEOUT"

    # API Key errors (API_KEY_*)
    API_KEY_NOT_FOUND = "API_KEY_NOT_FOUND"
    API_KEY_INVALID = "API_KEY_INVALID"
    API_KEY_EXPIRED = "API_KEY_EXPIRED"

    # Webhook errors (WEBHOOK_*)
    WEBHOOK_NOT_FOUND = "WEBHOOK_NOT_FOUND"
    WEBHOOK_DELIVERY_FAILED = "WEBHOOK_DELIVERY_FAILED"

    # Internal errors (INTERNAL_*)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INTERNAL_DATABASE_ERROR = "INTERNAL_DATABASE_ERROR"
    INTERNAL_SERVICE_UNAVAILABLE = "INTERNAL_SERVICE_UNAVAILABLE"


# Error messages by locale
ERROR_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        # Authentication
        ErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid email or password",
        ErrorCode.AUTH_INVALID_TOKEN: "Invalid or expired token",
        ErrorCode.AUTH_TOKEN_EXPIRED: "Token has expired",
        ErrorCode.AUTH_USER_DISABLED: "Account is disabled",
        ErrorCode.AUTH_USER_NOT_FOUND: "User not found",
        ErrorCode.AUTH_EMAIL_EXISTS: "Email already registered",
        ErrorCode.AUTH_UNAUTHORIZED: "Authentication required",
        # Validation
        ErrorCode.VALIDATION_ERROR: "Validation error",
        ErrorCode.VALIDATION_REQUIRED_FIELD: "Required field missing",
        ErrorCode.VALIDATION_INVALID_FORMAT: "Invalid format",
        ErrorCode.VALIDATION_MIN_PATTERNS: "At least {min} patterns must be enabled",
        ErrorCode.VALIDATION_INVALID_PROVIDER: "Provider must be 'bing', 'serper' or empty",
        # Resources
        ErrorCode.RESOURCE_NOT_FOUND: "Resource not found",
        ErrorCode.RESOURCE_ALREADY_EXISTS: "Resource already exists",
        ErrorCode.RESOURCE_CONFLICT: "Resource conflict",
        # Leads
        ErrorCode.LEAD_NOT_FOUND: "Lead not found",
        ErrorCode.LEAD_OPT_OUT: "Lead has opted out",
        ErrorCode.LEAD_NO_VERIFICATION_LOG: "No verification log for this lead",
        # Jobs
        ErrorCode.JOB_NOT_FOUND: "Job not found",
        ErrorCode.JOB_INVALID_STATE: "Cannot perform action on job in state {state}",
        ErrorCode.JOB_TIMEOUT: "Job execution timeout exceeded",
        # Quotas
        ErrorCode.QUOTA_EXCEEDED: "Quota exceeded",
        ErrorCode.QUOTA_API_KEYS_LIMIT: "Maximum API keys limit reached: {max}",
        ErrorCode.QUOTA_VERIFICATIONS_LIMIT: "Verification quota exceeded for this period",
        # Verification
        ErrorCode.VERIFY_INVALID_EMAIL: "Invalid email format",
        ErrorCode.VERIFY_DOMAIN_NOT_FOUND: "Domain not found or invalid",
        ErrorCode.VERIFY_SMTP_BLOCKED: "SMTP verification unavailable (port 25 blocked)",
        ErrorCode.VERIFY_TIMEOUT: "Verification timed out",
        # API Keys
        ErrorCode.API_KEY_NOT_FOUND: "API key not found",
        ErrorCode.API_KEY_INVALID: "Invalid API key",
        ErrorCode.API_KEY_EXPIRED: "API key has expired",
        # Webhooks
        ErrorCode.WEBHOOK_NOT_FOUND: "Webhook not found",
        ErrorCode.WEBHOOK_DELIVERY_FAILED: "Webhook delivery failed",
        # Internal
        ErrorCode.INTERNAL_ERROR: "Internal server error",
        ErrorCode.INTERNAL_DATABASE_ERROR: "Database error",
        ErrorCode.INTERNAL_SERVICE_UNAVAILABLE: "Service temporarily unavailable",
    },
    "es": {
        # Authentication
        ErrorCode.AUTH_INVALID_CREDENTIALS: "Email o contraseña inválidos",
        ErrorCode.AUTH_INVALID_TOKEN: "Token inválido o expirado",
        ErrorCode.AUTH_TOKEN_EXPIRED: "El token ha expirado",
        ErrorCode.AUTH_USER_DISABLED: "La cuenta está deshabilitada",
        ErrorCode.AUTH_USER_NOT_FOUND: "Usuario no encontrado",
        ErrorCode.AUTH_EMAIL_EXISTS: "El email ya está registrado",
        ErrorCode.AUTH_UNAUTHORIZED: "Autenticación requerida",
        # Validation
        ErrorCode.VALIDATION_ERROR: "Error de validación",
        ErrorCode.VALIDATION_REQUIRED_FIELD: "Campo requerido no proporcionado",
        ErrorCode.VALIDATION_INVALID_FORMAT: "Formato inválido",
        ErrorCode.VALIDATION_MIN_PATTERNS: "Debe haber al menos {min} patrones habilitados",
        ErrorCode.VALIDATION_INVALID_PROVIDER: "El proveedor debe ser 'bing', 'serper' o vacío",
        # Resources
        ErrorCode.RESOURCE_NOT_FOUND: "Recurso no encontrado",
        ErrorCode.RESOURCE_ALREADY_EXISTS: "El recurso ya existe",
        ErrorCode.RESOURCE_CONFLICT: "Conflicto de recursos",
        # Leads
        ErrorCode.LEAD_NOT_FOUND: "Lead no encontrado",
        ErrorCode.LEAD_OPT_OUT: "El lead ha solicitado baja (opt-out)",
        ErrorCode.LEAD_NO_VERIFICATION_LOG: "No hay log de verificación para este lead",
        # Jobs
        ErrorCode.JOB_NOT_FOUND: "Job no encontrado",
        ErrorCode.JOB_INVALID_STATE: "No se puede realizar la acción en un job en estado {state}",
        ErrorCode.JOB_TIMEOUT: "Tiempo de ejecución del job excedido",
        # Quotas
        ErrorCode.QUOTA_EXCEEDED: "Cuota excedida",
        ErrorCode.QUOTA_API_KEYS_LIMIT: "Límite máximo de API keys alcanzado: {max}",
        ErrorCode.QUOTA_VERIFICATIONS_LIMIT: "Cuota de verificaciones excedida para este período",
        # Verification
        ErrorCode.VERIFY_INVALID_EMAIL: "Formato de email inválido",
        ErrorCode.VERIFY_DOMAIN_NOT_FOUND: "Dominio no encontrado o inválido",
        ErrorCode.VERIFY_SMTP_BLOCKED: "Verificación SMTP no disponible (puerto 25 bloqueado)",
        ErrorCode.VERIFY_TIMEOUT: "Tiempo de verificación excedido",
        # API Keys
        ErrorCode.API_KEY_NOT_FOUND: "API key no encontrada",
        ErrorCode.API_KEY_INVALID: "API key inválida",
        ErrorCode.API_KEY_EXPIRED: "La API key ha expirado",
        # Webhooks
        ErrorCode.WEBHOOK_NOT_FOUND: "Webhook no encontrado",
        ErrorCode.WEBHOOK_DELIVERY_FAILED: "Fallo en la entrega del webhook",
        # Internal
        ErrorCode.INTERNAL_ERROR: "Error interno del servidor",
        ErrorCode.INTERNAL_DATABASE_ERROR: "Error de base de datos",
        ErrorCode.INTERNAL_SERVICE_UNAVAILABLE: "Servicio temporalmente no disponible",
    },
}

# Default locale
DEFAULT_LOCALE = "es"

# Supported locales
SUPPORTED_LOCALES = ["en", "es"]


def get_error_message(code: str | ErrorCode, locale: str = DEFAULT_LOCALE, **kwargs: str) -> str:
    """Get localized error message for a given error code.

    Args:
        code: Error code (string or ErrorCode enum)
        locale: Language code (en, es)
        **kwargs: Placeholder values for message formatting

    Returns:
        Localized error message, with placeholders replaced if provided.
    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    code_str = code.value if isinstance(code, ErrorCode) else code
    messages = ERROR_MESSAGES.get(locale, ERROR_MESSAGES[DEFAULT_LOCALE])
    message = messages.get(code_str, f"Error: {code_str}")

    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # If placeholder not found, return message as-is

    return message


def get_all_error_codes(locale: str = DEFAULT_LOCALE) -> dict[str, str]:
    """Get all error codes with their localized messages.

    Args:
        locale: Language code (en, es)

    Returns:
        Dictionary mapping error codes to their localized messages.
    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    return {code.value: ERROR_MESSAGES[locale].get(code.value, code.value) for code in ErrorCode}
