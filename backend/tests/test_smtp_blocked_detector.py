"""Tests for SMTP blocked detector and new verification signals."""
from __future__ import annotations

from app.services.verification.dns_checker import detect_provider
from app.services.verification.result import VerifyResult


class TestProviderDetection:
    """Tests for provider detection from MX records."""

    def test_detect_google_provider(self):
        """Should detect Google from MX."""
        mx_hosts = [(10, "alt1.aspmx.l.google.com"), (5, "aspmx.l.google.com")]
        result = detect_provider(mx_hosts)

        assert result == "google"

    def test_detect_microsoft_provider(self):
        """Should detect Microsoft from MX."""
        mx_hosts = [(0, "empresa-com.mail.protection.outlook.com")]
        result = detect_provider(mx_hosts)

        assert result == "microsoft"

    def test_detect_ionos_provider(self):
        """Should detect IONOS from MX."""
        mx_hosts = [(10, "mx00.ionos.es")]
        result = detect_provider(mx_hosts)

        assert result == "ionos"

    def test_detect_barracuda_provider(self):
        """Should detect Barracuda from MX."""
        mx_hosts = [(10, "mx1.ess.de.barracudanetworks.com")]
        result = detect_provider(mx_hosts)

        assert result == "barracuda"

    def test_detect_other_provider(self):
        """Should return 'other' for unknown MX."""
        mx_hosts = [(10, "mail.custom-server.net")]
        result = detect_provider(mx_hosts)

        assert result == "other"

    def test_detect_empty_mx_list(self):
        """Should return 'other' for empty MX list."""
        result = detect_provider([])

        assert result == "other"

    def test_detect_uses_first_match(self):
        """Should use first matching provider by MX preference."""
        # Mixed providers, Google has lower preference (higher priority)
        mx_hosts = [(5, "aspmx.l.google.com"), (10, "mail.protection.outlook.com")]
        result = detect_provider(mx_hosts)

        assert result == "google"


class TestVerifyResultSignals:
    """Tests for new signal fields in VerifyResult."""

    def test_verify_result_has_new_fields(self):
        """VerifyResult should have new signal fields."""
        result = VerifyResult(
            email="test@example.com",
            status="risky",
            reason="Test reason",
            confidence_score=65,
            mx_found=True,
            spf_present=True,
            dmarc_present=True,
            smtp_blocked=True,
            provider="google",
            signals=["mx", "spf", "dmarc"],
        )

        assert result.spf_present is True
        assert result.dmarc_present is True
        assert result.smtp_blocked is True
        assert result.smtp_attempted is False  # default
        assert result.provider == "google"
        assert "mx" in result.signals
        assert "spf" in result.signals
        assert "dmarc" in result.signals

    def test_verify_result_default_values(self):
        """VerifyResult should have sensible defaults."""
        result = VerifyResult(
            email="test@example.com",
            status="unknown",
            reason="Minimal",
            confidence_score=50,
            mx_found=True,
        )

        assert result.spf_present is False
        assert result.dmarc_present is False
        assert result.smtp_blocked is False
        assert result.smtp_attempted is False
        assert result.provider == "other"
        assert result.signals == []
        assert result.catch_all is None
        assert result.web_mentioned is False

    def test_verify_result_catch_all_nullable(self):
        """catch_all should accept None (not attempted)."""
        result = VerifyResult(
            email="test@example.com",
            status="risky",
            reason="SMTP not attempted",
            confidence_score=55,
            mx_found=True,
            catch_all=None,
        )

        assert result.catch_all is None


class TestVerifyEmailWithSmtpBlocked:
    """Tests for verify_email behavior when SMTP is blocked."""

    def test_verify_email_includes_provider(self, mock_dns_valid, mock_smtp_valid):
        """verify_email should include provider in result."""
        from app.services.verification import verify_email

        result = verify_email("test@example.com")

        # Provider detection depends on MX hostname
        assert hasattr(result, "provider")
        assert result.provider in ("google", "microsoft", "other", "ionos", "barracuda", "proofpoint", "mimecast", "ovh", "zoho", "yahoo", "icloud")

    def test_verify_email_includes_spf_dmarc(self, mock_dns_valid, mock_smtp_valid):
        """verify_email should include SPF/DMARC signals."""
        from app.services.verification import verify_email

        result = verify_email("test@example.com")

        assert hasattr(result, "spf_present")
        assert hasattr(result, "dmarc_present")
        # With mock_dns_valid, SPF should be detected
        assert result.spf_present is True

    def test_verify_email_populates_signals_list(self, mock_dns_valid, mock_smtp_valid):
        """verify_email should populate signals list."""
        from app.services.verification import verify_email

        result = verify_email("test@example.com")

        assert hasattr(result, "signals")
        assert isinstance(result.signals, list)
        # MX should always be in signals if found
        if result.mx_found:
            assert "mx" in result.signals

    def test_verify_email_smtp_attempted_tracked(self, mock_dns_valid, mock_smtp_valid):
        """verify_email should track if SMTP was attempted."""
        from app.services.verification import verify_email

        result = verify_email("test@example.com")

        assert hasattr(result, "smtp_attempted")
        # With valid mocks, SMTP should be attempted
        assert result.smtp_attempted is True


class TestSmtpBlockedDetectorUnit:
    """Unit tests for smtp_blocked_detector functions."""

    def test_threshold_constant_is_reasonable(self):
        """Threshold should be at least 2 hosts."""
        from app.services.smtp_blocked_detector import THRESHOLD_HOSTS

        assert THRESHOLD_HOSTS >= 2
        assert THRESHOLD_HOSTS <= 10

    def test_window_constant_is_reasonable(self):
        """Window should be between 1 and 10 minutes."""
        from app.services.smtp_blocked_detector import WINDOW_SECONDS

        assert WINDOW_SECONDS >= 60
        assert WINDOW_SECONDS <= 600

    def test_ttl_constant_is_reasonable(self):
        """TTL should be between 5 and 30 minutes."""
        from app.services.smtp_blocked_detector import TTL_BLOCKED_SECONDS

        assert TTL_BLOCKED_SECONDS >= 300
        assert TTL_BLOCKED_SECONDS <= 1800


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility for API consumers."""

    def test_verify_result_serializable_without_new_fields(self):
        """Old clients should work without new fields (defaults used)."""
        result = VerifyResult(
            email="test@example.com",
            status="risky",
            reason="Test",
            confidence_score=60,
            mx_found=True,
        )

        # Simulate old client accessing only original fields
        data = {
            "email": result.email,
            "status": result.status,
            "confidence_score": result.confidence_score,
            "mx_found": result.mx_found,
            "smtp_check": result.smtp_check,  # deprecated but kept
        }

        assert data["email"] == "test@example.com"
        assert data["status"] == "risky"
        assert data["confidence_score"] == 60
        assert data["mx_found"] is True
        assert data["smtp_check"] is False  # default

    def test_verify_candidate_schema_has_defaults(self):
        """VerifyCandidate schema should have sensible defaults."""
        from app.schemas.verify import VerifyCandidate

        # Minimal data (old client might send)
        candidate = VerifyCandidate(
            email="test@example.com",
            status="valid",
            confidence_score=90,
        )

        # New fields should have defaults
        assert candidate.mx_found is False  # default
        assert candidate.spf_present is False
        assert candidate.dmarc_present is False
        assert candidate.catch_all is None
        assert candidate.smtp_attempted is False
        assert candidate.smtp_blocked is False
        assert candidate.provider == "other"
        assert candidate.web_mentioned is False
        assert candidate.signals == []
        assert candidate.reason == ""

    def test_lead_response_schema_backward_compatible(self):
        """LeadResponse should maintain backward compatibility."""
        from datetime import datetime

        from app.schemas.lead import LeadResponse

        # All required fields for LeadResponse
        lead_data = {
            "id": 1,
            "workspace_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "company": "Test Inc",
            "domain": "test.com",
            "email_best": "john.doe@test.com",
            "verification_status": "valid",
            "confidence_score": 85,
            "mx_found": True,
            "catch_all": False,
            "smtp_check": True,
            "notes": "",
            "sales_status": "new",
            "source": "manual",
            "title": "Engineer",
            "linkedin_url": "",
            "lawful_basis": "legitimate_interest",
            "purpose": "sales",
            "opt_out": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # Should not raise - new fields have defaults
        lead = LeadResponse(**lead_data)

        # New fields should have defaults
        assert lead.spf_present is False
        assert lead.dmarc_present is False
        assert lead.smtp_attempted is False
        assert lead.smtp_blocked is False
        assert lead.provider == "other"
        assert lead.signals == []


# Import mocks from mocks.py
pytest_plugins = ["tests.mocks"]
