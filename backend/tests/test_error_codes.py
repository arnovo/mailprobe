"""Tests for error codes and i18n endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.error_codes import (
    DEFAULT_LOCALE,
    ERROR_MESSAGES,
    SUPPORTED_LOCALES,
    ErrorCode,
    get_all_error_codes,
    get_error_message,
)


class TestErrorCodeConstants:
    """Tests for error code constants and enums."""

    def test_error_code_enum_has_values(self):
        """ErrorCode enum should have multiple values."""
        assert len(list(ErrorCode)) > 10

    def test_default_locale_is_spanish(self):
        """Default locale should be Spanish."""
        assert DEFAULT_LOCALE == "es"
        assert set(SUPPORTED_LOCALES) == {"en", "es"}

    @pytest.mark.parametrize("code", list(ErrorCode))
    def test_error_code_is_valid_string(self, code: ErrorCode):
        """Each error code should be a non-empty string."""
        assert isinstance(code.value, str) and len(code.value) > 0

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_all_codes_have_message_in_locale(self, locale: str):
        """Every error code should have a message in each supported locale."""
        messages = ERROR_MESSAGES.get(locale, {})
        for code in ErrorCode:
            assert code.value in messages, f"Missing {code.value} in locale {locale}"


class TestGetErrorMessage:
    """Tests for get_error_message function."""

    @pytest.mark.parametrize(
        "code,locale,expected",
        [
            (ErrorCode.AUTH_INVALID_CREDENTIALS, "en", "Invalid email or password"),
            (ErrorCode.AUTH_INVALID_CREDENTIALS, "es", "Email o contraseña inválidos"),
            ("AUTH_INVALID_CREDENTIALS", "en", "Invalid email or password"),  # string code
            (ErrorCode.AUTH_INVALID_CREDENTIALS, "fr", "Email o contraseña inválidos"),  # fallback
        ],
    )
    def test_get_message(self, code, locale: str, expected: str):
        """Should return correct message for code and locale."""
        assert get_error_message(code, locale) == expected

    def test_get_message_with_placeholder(self):
        """Should replace placeholders in message."""
        msg = get_error_message(ErrorCode.VALIDATION_MIN_PATTERNS, "en", min="3")
        assert "3" in msg

    def test_unknown_code_returns_code_itself(self):
        """Unknown code should return the code itself."""
        assert "UNKNOWN_XYZ" in get_error_message("UNKNOWN_XYZ", "en")


class TestGetAllErrorCodes:
    """Tests for get_all_error_codes function."""

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES + ["xyz"])
    def test_returns_dict_with_all_codes(self, locale: str):
        """Should return dictionary with all enum codes for any locale."""
        codes = get_all_error_codes(locale)
        assert isinstance(codes, dict) and len(codes) > 10
        for code in ErrorCode:
            assert code.value in codes


class TestI18nEndpoints:
    """Tests for i18n API endpoints."""

    @pytest.mark.asyncio
    async def test_list_locales(self, client: AsyncClient):
        """GET /v1/i18n/locales should return supported locales."""
        response = await client.get("/v1/i18n/locales")
        assert response.status_code == 200
        data = response.json()["data"]
        assert set(data["locales"]) == {"en", "es"}
        assert data["default"] == "es"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "locale,expected_msg",
        [
            ("", "Email o contraseña inválidos"),  # default (es)
            ("en", "Invalid email or password"),
            ("es", "Email o contraseña inválidos"),
        ],
    )
    async def test_list_error_codes(self, client: AsyncClient, locale: str, expected_msg: str):
        """GET /v1/i18n/error-codes should return codes in requested locale."""
        url = f"/v1/i18n/error-codes?locale={locale}" if locale else "/v1/i18n/error-codes"
        response = await client.get(url)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["codes"]["AUTH_INVALID_CREDENTIALS"] == expected_msg

    @pytest.mark.asyncio
    async def test_get_single_error_code(self, client: AsyncClient):
        """GET /v1/i18n/error-codes/{code} should return single code."""
        response = await client.get("/v1/i18n/error-codes/AUTH_INVALID_CREDENTIALS?locale=en")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data == {
            "code": "AUTH_INVALID_CREDENTIALS",
            "message": "Invalid email or password",
            "locale": "en",
        }

    @pytest.mark.asyncio
    async def test_get_unknown_error_code(self, client: AsyncClient):
        """GET /v1/i18n/error-codes/{unknown} should return 404."""
        response = await client.get("/v1/i18n/error-codes/UNKNOWN_CODE_XYZ")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


class TestAuthErrorCodes:
    """Tests that auth endpoints return standardized ErrorCode values."""

    @pytest.mark.asyncio
    async def test_login_invalid_credentials_returns_auth_code(self, client: AsyncClient):
        """POST /v1/auth/login with wrong password should return AUTH_INVALID_CREDENTIALS."""
        response = await client.post(
            "/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrong"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("error") is not None
        assert data["error"]["code"] == ErrorCode.AUTH_INVALID_CREDENTIALS.value
