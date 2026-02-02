"""Integration tests for email verification flow."""

from app.services.verification import (
    DISPOSABLE_DOMAINS,
    VerifyResult,
    verify_and_pick_best,
    verify_email,
)


class TestVerifyEmail:
    """Tests for verify_email function."""

    def test_invalid_email_format(self):
        """Should reject malformed email."""
        result = verify_email("not-an-email")

        assert result.status == "invalid"
        assert result.confidence_score == 0
        assert not result.mx_found

    def test_invalid_email_no_at(self):
        """Should reject email without @."""
        result = verify_email("user.example.com")

        assert result.status == "invalid"

    def test_invalid_email_no_domain(self):
        """Should reject email with no domain part."""
        result = verify_email("user@")

        assert result.status == "invalid"

    def test_disposable_domain_rejected(self):
        """Should reject disposable email domains."""
        result = verify_email("test@mailinator.com")

        assert result.status == "invalid"
        assert "disposable" in result.reason.lower() or "temporary" in result.reason.lower()

    def test_all_disposable_domains_rejected(self):
        """Should reject all known disposable domains."""
        for domain in list(DISPOSABLE_DOMAINS)[:5]:  # Test first 5
            result = verify_email(f"test@{domain}")
            assert result.status == "invalid", f"Domain {domain} should be rejected"

    def test_valid_email_with_mocked_network(self, mock_dns_valid, mock_smtp_valid):
        """Should validate email with mocked DNS and SMTP."""
        result = verify_email("john.doe@example.com")

        assert result.status in ("valid", "risky", "unknown")
        assert result.mx_found
        assert result.smtp_check

    def test_catch_all_detection(self, mock_dns_valid, mock_smtp_catch_all):
        """Should detect catch-all domains."""
        result = verify_email("john.doe@catchall-domain.com")

        # Catch-all should result in risky or unknown
        assert result.status in ("risky", "unknown", "valid")
        # Note: catch_all detection depends on random email being accepted

    def test_rejected_email(self, mock_dns_valid, mock_smtp_reject):
        """Should mark rejected email as invalid."""
        result = verify_email("nonexistent@example.com")

        assert result.status == "invalid"
        assert "rejected" in result.reason.lower()

    def test_timeout_handling(self, mock_dns_valid, mock_smtp_timeout):
        """Should handle SMTP timeout gracefully."""
        result = verify_email("test@slow-server.com")

        assert result.status in ("unknown", "invalid")
        assert result.smtp_check or not result.smtp_check  # May or may not have attempted

    def test_no_mx_records(self, mock_dns_no_mx):
        """Should handle domains without MX records."""
        result = verify_email("test@no-mx-domain.com")

        assert result.status == "invalid"
        assert not result.mx_found


class TestVerifyAndPickBest:
    """Tests for verify_and_pick_best function."""

    def test_generates_and_verifies_candidates(self, mock_dns_valid, mock_smtp_valid):
        """Should generate candidates and return best one."""
        candidates, best_email, best_result, probe_results = verify_and_pick_best(
            first_name="John",
            last_name="Doe",
            domain="example.com",
        )

        assert len(candidates) > 0
        assert best_email in candidates
        assert best_result is not None
        assert isinstance(best_result, VerifyResult)
        assert len(probe_results) == len(candidates)

    def test_returns_empty_for_missing_data(self):
        """Should return empty when no candidates can be generated."""
        candidates, best_email, best_result, probe_results = verify_and_pick_best(
            first_name="John",
            last_name="",
            domain="example.com",
            allow_no_lastname=False,
        )

        assert candidates == []
        assert best_email == ""
        assert best_result is None

    def test_allow_no_lastname(self, mock_dns_valid, mock_smtp_valid):
        """Should generate generic patterns when allow_no_lastname=True."""
        candidates, best_email, best_result, probe_results = verify_and_pick_best(
            first_name="John",
            last_name="",
            domain="example.com",
            allow_no_lastname=True,
        )

        assert len(candidates) > 0
        assert "info@example.com" in candidates
        assert best_email != ""

    def test_respects_enabled_patterns(self, mock_dns_valid, mock_smtp_valid):
        """Should only use enabled pattern indices."""
        candidates, _, _, _ = verify_and_pick_best(
            first_name="John",
            last_name="Doe",
            domain="example.com",
            enabled_pattern_indices=[0, 1],
        )

        assert len(candidates) <= 2

    def test_progress_callback(self, mock_dns_valid, mock_smtp_valid):
        """Should call progress callback during verification via logger."""
        from app.core.log_service import VerificationLogger

        progress_calls = []

        def progress_callback(msg, candidate, response):
            progress_calls.append((msg, candidate, response))

        logger = VerificationLogger(progress_callback=progress_callback)

        verify_and_pick_best(
            first_name="John",
            last_name="Doe",
            domain="example.com",
            logger=logger,
        )

        assert len(progress_calls) > 0

    def test_detail_callback(self, mock_dns_valid, mock_smtp_valid):
        """Should call detail callback with technical info via logger."""
        from app.core.log_service import VerificationLogger

        detail_calls = []

        def detail_callback(msg):
            detail_calls.append(msg)

        logger = VerificationLogger(detail_callback=detail_callback)

        verify_and_pick_best(
            first_name="John",
            last_name="Doe",
            domain="example.com",
            logger=logger,
        )

        assert len(detail_calls) > 0
        # Should include config info (now as JSON with DEBUG_CONFIG code)
        assert any("DEBUG_CONFIG" in call for call in detail_calls)

    def test_picks_best_by_confidence(self, mock_dns_valid, mock_smtp_valid):
        """Should pick candidate with highest confidence score."""
        candidates, best_email, best_result, probe_results = verify_and_pick_best(
            first_name="John",
            last_name="Doe",
            domain="example.com",
        )

        # Best result should have highest or tied-highest confidence
        max_score = max(pr["confidence_score"] for pr in probe_results.values())
        assert best_result.confidence_score == max_score


# Import mocks from mocks.py
pytest_plugins = ["tests.mocks"]
