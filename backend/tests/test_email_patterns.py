"""Unit tests for email pattern generation."""

from app.services.email_patterns import generate_candidates


class TestGenerateCandidates:
    """Tests for generate_candidates function."""
    
    def test_generates_candidates_with_full_name(self):
        """Should generate standard email patterns with first and last name."""
        candidates = generate_candidates("John", "Doe", "example.com")
        
        assert len(candidates) > 0
        # Check some expected patterns
        assert "john.doe@example.com" in candidates
        assert "jdoe@example.com" in candidates
        assert "john@example.com" in candidates
        assert "johndoe@example.com" in candidates
    
    def test_generates_candidates_case_insensitive(self):
        """Should normalize names to lowercase."""
        candidates = generate_candidates("JOHN", "DOE", "EXAMPLE.COM")
        
        for email in candidates:
            assert email == email.lower()
    
    def test_handles_compound_names(self):
        """Should handle compound first names."""
        candidates = generate_candidates("Juan Carlos", "García", "example.com")
        
        assert len(candidates) > 0
        # First part of compound name should be used
        assert any("juan" in c for c in candidates)
    
    def test_handles_special_characters(self):
        """Should handle accented characters."""
        candidates = generate_candidates("José", "González", "example.com")
        
        assert len(candidates) > 0
        # Should normalize accented characters
        assert any("jose" in c or "josé" in c for c in candidates)
    
    def test_no_lastname_not_allowed_returns_empty(self):
        """Should return empty list when no lastname and allow_no_lastname=False."""
        candidates = generate_candidates("John", "", "example.com", allow_no_lastname=False)
        
        assert candidates == []
    
    def test_no_lastname_allowed_returns_generic_patterns(self):
        """Should return generic patterns when no lastname and allow_no_lastname=True."""
        candidates = generate_candidates("John", "", "example.com", allow_no_lastname=True)
        
        assert len(candidates) > 0
        # Should include generic patterns
        assert "info@example.com" in candidates
        assert "contact@example.com" in candidates
    
    def test_respects_max_candidates(self):
        """Should respect max_candidates limit."""
        candidates = generate_candidates("John", "Doe", "example.com", max_candidates=5)
        
        assert len(candidates) <= 5
    
    def test_respects_enabled_pattern_indices(self):
        """Should only use enabled pattern indices when specified."""
        # Get all candidates first
        all_candidates = generate_candidates("John", "Doe", "example.com")
        
        # Now limit to first 3 patterns
        limited = generate_candidates(
            "John", "Doe", "example.com",
            enabled_pattern_indices=[0, 1, 2]
        )
        
        assert len(limited) <= len(all_candidates)
        assert len(limited) <= 3
    
    def test_empty_domain_returns_empty(self):
        """Should return empty list for empty domain."""
        candidates = generate_candidates("John", "Doe", "")
        
        assert candidates == []
    
    def test_whitespace_in_names_handled(self):
        """Should handle whitespace in names."""
        candidates = generate_candidates("  John  ", "  Doe  ", "example.com")
        
        assert len(candidates) > 0
        for email in candidates:
            assert "  " not in email
    
    def test_no_duplicates(self):
        """Should not return duplicate candidates."""
        candidates = generate_candidates("John", "Doe", "example.com")
        
        assert len(candidates) == len(set(candidates))
