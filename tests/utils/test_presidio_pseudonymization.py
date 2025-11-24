"""
Unit tests for Phase 2.2: Entity Pseudonymization and PII Detection

Tests cover:
1. EntityPseudonymizer class functionality
2. Presidio integration with pseudonymization
3. Consistency and semantic preservation
4. Edge cases and error handling
5. Integration with sanitization pipeline
"""

import pytest
from ai_tester.utils.data_sanitizer import (
    EntityPseudonymizer,
    pseudonymize_text_with_presidio,
    sanitize_jira_ticket_with_pseudonymization,
    PRESIDIO_AVAILABLE
)


# ============================================================================
# ENTITY PSEUDONYMIZER TESTS
# ============================================================================

class TestEntityPseudonymizer:
    """Tests for EntityPseudonymizer class"""

    def test_initialization(self):
        """Test pseudonymizer initializes with empty mappings"""
        pseudonymizer = EntityPseudonymizer()

        assert len(pseudonymizer.entity_to_placeholder) == 0
        assert len(pseudonymizer.placeholder_to_entity) == 0
        assert len(pseudonymizer.counters) == 0
        assert pseudonymizer._contains_sensitive_data is True

    def test_consistent_placeholders(self):
        """Test that same entity gets same placeholder"""
        pseudonymizer = EntityPseudonymizer()

        email = "john@company.com"
        placeholder1 = pseudonymizer.pseudonymize_entity(email, "EMAIL_ADDRESS")
        placeholder2 = pseudonymizer.pseudonymize_entity(email, "EMAIL_ADDRESS")

        assert placeholder1 == placeholder2
        assert placeholder1 == "<EMAIL_1>"

    def test_different_entities_get_different_placeholders(self):
        """Test that different entities get different placeholders"""
        pseudonymizer = EntityPseudonymizer()

        email1 = "john@company.com"
        email2 = "jane@company.com"

        placeholder1 = pseudonymizer.pseudonymize_entity(email1, "EMAIL_ADDRESS")
        placeholder2 = pseudonymizer.pseudonymize_entity(email2, "EMAIL_ADDRESS")

        assert placeholder1 != placeholder2
        assert placeholder1 == "<EMAIL_1>"
        assert placeholder2 == "<EMAIL_2>"

    def test_semantic_type_mapping(self):
        """Test that entity types are mapped to semantic placeholders"""
        pseudonymizer = EntityPseudonymizer()

        # Test various entity types
        email = pseudonymizer.pseudonymize_entity("test@example.com", "EMAIL_ADDRESS")
        ip = pseudonymizer.pseudonymize_entity("10.0.0.1", "IP_ADDRESS")
        phone = pseudonymizer.pseudonymize_entity("555-1234", "PHONE_NUMBER")

        assert email == "<EMAIL_1>"
        assert ip == "<IP_ADDRESS_1>"
        assert phone == "<PHONE_1>"

    def test_reverse_pseudonymization(self):
        """Test reverse mapping for debugging"""
        pseudonymizer = EntityPseudonymizer()

        original = "Contact john@company.com at IP 10.0.0.1"
        email = "john@company.com"
        ip = "10.0.0.1"

        placeholder_email = pseudonymizer.pseudonymize_entity(email, "EMAIL_ADDRESS")
        placeholder_ip = pseudonymizer.pseudonymize_entity(ip, "IP_ADDRESS")

        pseudonymized = original.replace(email, placeholder_email).replace(ip, placeholder_ip)
        assert "john@company.com" not in pseudonymized
        assert "10.0.0.1" not in pseudonymized

        # Reverse it
        reversed_text = pseudonymizer.reverse_pseudonymization(pseudonymized)
        assert reversed_text == original

    def test_get_summary(self):
        """Test audit summary generation"""
        pseudonymizer = EntityPseudonymizer()

        pseudonymizer.pseudonymize_entity("john@example.com", "EMAIL_ADDRESS")
        pseudonymizer.pseudonymize_entity("jane@example.com", "EMAIL_ADDRESS")
        pseudonymizer.pseudonymize_entity("10.0.0.1", "IP_ADDRESS")

        summary = pseudonymizer.get_summary()

        assert summary["total_entities"] == 3
        assert summary["by_type"]["EMAIL"] == 2
        assert summary["by_type"]["IP_ADDRESS"] == 1
        assert "note" in summary
        assert "Entity mappings not included" in summary["note"]

    def test_cannot_pickle_pseudonymizer(self):
        """Test that pseudonymizer cannot be pickled (security)"""
        import pickle
        pseudonymizer = EntityPseudonymizer()
        pseudonymizer.pseudonymize_entity("secret@example.com", "EMAIL_ADDRESS")

        with pytest.raises(TypeError) as exc_info:
            pickle.dumps(pseudonymizer)

        assert "cannot be pickled" in str(exc_info.value).lower()
        assert "PII mappings must stay in memory" in str(exc_info.value)

    def test_multiple_entity_types(self):
        """Test handling multiple entity types"""
        pseudonymizer = EntityPseudonymizer()

        entities = [
            ("john@example.com", "EMAIL_ADDRESS"),
            ("10.0.0.1", "IP_ADDRESS"),
            ("555-1234", "PHONE_NUMBER"),
            ("4111-1111-1111-1111", "CREDIT_CARD"),
        ]

        placeholders = [pseudonymizer.pseudonymize_entity(val, typ) for val, typ in entities]

        # Check all different
        assert len(set(placeholders)) == 4

        # Check semantic names
        assert placeholders[0] == "<EMAIL_1>"
        assert placeholders[1] == "<IP_ADDRESS_1>"
        assert placeholders[2] == "<PHONE_1>"
        assert placeholders[3] == "<CREDIT_CARD_1>"


# ============================================================================
# PRESIDIO INTEGRATION TESTS
# ============================================================================

@pytest.mark.skipif(not PRESIDIO_AVAILABLE, reason="Presidio not installed")
class TestPresidioIntegration:
    """Tests for Presidio integration with pseudonymization"""

    def test_detect_email_in_text(self):
        """Test email detection in narrative text"""
        text = "Contact support at support@example.com for help"
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        # Email should be replaced
        assert "support@example.com" not in pseudonymized
        assert "<EMAIL_1>" in pseudonymized

        # Summary should show detection
        assert summary["entities_detected"] == 1
        assert summary["by_type"]["EMAIL"] == 1

    def test_detect_ip_address(self):
        """Test IP address detection"""
        text = "Server is at 10.0.45.23 for internal access"
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        assert "10.0.45.23" not in pseudonymized
        assert "<IP_ADDRESS_1>" in pseudonymized
        assert summary["entities_detected"] == 1

    def test_detect_phone_number(self):
        """Test phone number detection"""
        text = "Call us at 555-123-4567 for support"
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        assert "555-123-4567" not in pseudonymized
        assert "<PHONE_" in pseudonymized
        assert summary["entities_detected"] >= 1  # May detect variations

    def test_multiple_entities_same_type(self):
        """Test multiple entities of same type get different placeholders"""
        text = "Contact john@company.com or jane@company.com"
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        assert "john@company.com" not in pseudonymized
        assert "jane@company.com" not in pseudonymized
        assert "<EMAIL_1>" in pseudonymized
        assert "<EMAIL_2>" in pseudonymized
        assert summary["entities_detected"] == 2

    def test_consistency_across_multiple_mentions(self):
        """Test same entity gets same placeholder across text"""
        text = "Email john@company.com for access. Contact john@company.com again."
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        # Same email should map to same placeholder
        assert pseudonymized.count("<EMAIL_1>") == 2
        assert "<EMAIL_2>" not in pseudonymized
        assert summary["entities_detected"] == 2  # Two instances detected

    def test_preserves_text_structure(self):
        """Test that pseudonymization preserves text structure"""
        text = "Email john@company.com at IP 10.0.0.1 for access to the system."
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        # Structure should be preserved
        assert "Email" in pseudonymized
        assert "at IP" in pseudonymized
        assert "for access to the system" in pseudonymized

        # Sensitive data removed
        assert "john@company.com" not in pseudonymized
        assert "10.0.0.1" not in pseudonymized

    def test_empty_text(self):
        """Test handling of empty text"""
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio("", pseudonymizer)

        assert pseudonymized == ""
        assert summary["entities_detected"] == 0

    def test_text_with_no_pii(self):
        """Test text with no PII returns unchanged"""
        text = "This is a normal sentence with no sensitive information."
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        assert pseudonymized == text
        assert summary["entities_detected"] == 0

    def test_custom_entity_types(self):
        """Test custom entity type list"""
        text = "Contact john@company.com at 10.0.0.1"
        pseudonymizer = EntityPseudonymizer()

        # Only detect emails
        pseudonymized, summary = pseudonymize_text_with_presidio(
            text,
            pseudonymizer,
            entities_to_detect=["EMAIL_ADDRESS"]
        )

        assert "john@company.com" not in pseudonymized
        assert "10.0.0.1" in pseudonymized  # IP not detected
        assert summary["entities_detected"] == 1


# ============================================================================
# INTEGRATION WITH SANITIZATION PIPELINE
# ============================================================================

@pytest.mark.skipif(not PRESIDIO_AVAILABLE, reason="Presidio not installed")
class TestSanitizationPipelineIntegration:
    """Tests for integration with full sanitization pipeline"""

    def test_sanitize_ticket_with_pii_detection_disabled(self):
        """Test ticket sanitization with PII detection disabled"""
        ticket = {
            "key": "PROJ-123",
            "fields": {
                "summary": "Test ticket",
                "description": "Contact john@company.com for access",
                "reporter": {"emailAddress": "reporter@company.com"}  # Blocked by Phase 1
            }
        }

        sanitized, audit = sanitize_jira_ticket_with_pseudonymization(
            ticket,
            detect_pii=False
        )

        # PII detection disabled - email stays in description
        assert "john@company.com" in sanitized['fields']['description']

        # But reporter field removed by Phase 1
        assert "reporter" not in sanitized['fields']

        # Audit confirms PII detection was disabled
        assert audit["pii_detection_enabled"] is False
        assert audit["entities_replaced"] == 0

    def test_sanitize_ticket_with_pii_detection_enabled(self):
        """Test ticket sanitization with PII detection enabled"""
        ticket = {
            "key": "PROJ-456",
            "fields": {
                "summary": "Access issue",
                "description": "User john@company.com cannot access server at 10.0.45.23"
            }
        }

        sanitized, audit = sanitize_jira_ticket_with_pseudonymization(
            ticket,
            detect_pii=True
        )

        # PII should be pseudonymized
        desc = sanitized['fields']['description']
        assert "john@company.com" not in desc
        assert "10.0.45.23" not in desc
        assert "<EMAIL_1>" in desc
        assert "<IP_ADDRESS_1>" in desc

        # Audit confirms replacements
        assert audit["pii_detection_enabled"] is True
        assert audit["entities_replaced"] >= 2
        assert "EMAIL" in audit["entity_types"]
        assert "IP_ADDRESS" in audit["entity_types"]

    def test_combined_phase1_and_phase22_sanitization(self):
        """Test that Phase 1 and Phase 2.2 work together"""
        ticket = {
            "key": "PROJ-789",
            "fields": {
                "summary": "Bug fix",
                "description": "Contact admin@company.com. Code: ```python\napi_key='secret'\n```",
                "reporter": {"emailAddress": "reporter@company.com"},
                "comment": ["sensitive comment"]  # Blocked by Phase 1
            }
        }

        sanitized, audit = sanitize_jira_ticket_with_pseudonymization(
            ticket,
            remove_code=True,
            detect_pii=True
        )

        desc = sanitized['fields']['description']

        # Phase 1: Code blocks removed
        assert "api_key='secret'" not in desc
        assert "[CODE_BLOCK_REMOVED]" in desc

        # Phase 1: Blocked fields removed
        assert "reporter" not in sanitized['fields']
        assert "comment" not in sanitized['fields']

        # Phase 2.2: Email pseudonymized
        assert "admin@company.com" not in desc
        assert "<EMAIL_1>" in desc

    def test_empty_description_field(self):
        """Test handling of tickets with empty description"""
        ticket = {
            "key": "PROJ-101",
            "fields": {
                "summary": "Test",
                "description": ""
            }
        }

        sanitized, audit = sanitize_jira_ticket_with_pseudonymization(
            ticket,
            detect_pii=True
        )

        assert sanitized['fields']['description'] == ""
        assert audit["entities_replaced"] == 0

    def test_missing_description_field(self):
        """Test handling of tickets without description field"""
        ticket = {
            "key": "PROJ-102",
            "fields": {
                "summary": "Test"
            }
        }

        sanitized, audit = sanitize_jira_ticket_with_pseudonymization(
            ticket,
            detect_pii=True
        )

        assert audit["entities_replaced"] == 0


# ============================================================================
# ERROR HANDLING & EDGE CASES
# ============================================================================

class TestErrorHandling:
    """Tests for error handling and edge cases"""

    @pytest.mark.skipif(PRESIDIO_AVAILABLE, reason="Test for when Presidio NOT installed")
    def test_presidio_not_available(self):
        """Test graceful handling when Presidio not installed"""
        text = "Contact john@company.com"
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        # Should return original text
        assert pseudonymized == text
        assert "error" in summary
        assert "Presidio not installed" in summary["error"]

    @pytest.mark.skipif(not PRESIDIO_AVAILABLE, reason="Presidio not installed")
    def test_special_characters_in_text(self):
        """Test handling of special characters"""
        text = "Email: john@example.com\nIP: 10.0.0.1\tPhone: 555-1234"
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        # Newlines and tabs should be preserved
        assert "\n" in pseudonymized
        assert "\t" in pseudonymized

        # PII should be replaced
        assert "john@example.com" not in pseudonymized

    @pytest.mark.skipif(not PRESIDIO_AVAILABLE, reason="Presidio not installed")
    def test_unicode_text(self):
        """Test handling of Unicode characters"""
        text = "Contact: café@example.com or 日本@example.jp"
        pseudonymizer = EntityPseudonymizer()

        pseudonymized, summary = pseudonymize_text_with_presidio(text, pseudonymizer)

        # Should handle Unicode gracefully
        assert "café" in pseudonymized or "<EMAIL_" in pseudonymized
        assert isinstance(pseudonymized, str)
