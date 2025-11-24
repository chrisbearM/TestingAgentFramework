"""
Unit tests for data_sanitizer module

Tests cover:
1. Field whitelisting configuration
2. Code block removal
3. Jira ticket sanitization
4. Attachment sanitization
5. Image sanitization (Phase 2.1)
6. Sanitization summary generation
"""

import pytest
from ai_tester.utils.data_sanitizer import (
    FieldWhitelistConfig,
    SAFE_FIELDS,
    BLOCKED_FIELDS,
    remove_code_blocks,
    sanitize_jira_ticket,
    sanitize_ticket_description,
    sanitize_document_content,
    sanitize_attachment,
    sanitize_image_attachment,
    get_sanitization_summary,
)


# ============================================================================
# FIELD WHITELISTING TESTS
# ============================================================================

class TestFieldWhitelistConfig:
    """Tests for FieldWhitelistConfig class"""

    def test_default_config_initialization(self):
        """Test that default config initializes with predefined safe/blocked fields"""
        config = FieldWhitelistConfig()

        assert config.safe_fields == SAFE_FIELDS
        assert config.blocked_fields == BLOCKED_FIELDS

    def test_custom_safe_fields(self):
        """Test initialization with custom safe fields"""
        custom_safe = {'field1', 'field2', 'field3'}
        config = FieldWhitelistConfig(safe_fields=custom_safe)

        assert config.safe_fields == custom_safe

    def test_custom_blocked_fields(self):
        """Test initialization with custom blocked fields"""
        custom_blocked = {'sensitive1', 'sensitive2'}
        config = FieldWhitelistConfig(blocked_fields=custom_blocked)

        assert config.blocked_fields == custom_blocked

    def test_additional_acceptance_criteria_fields(self):
        """Test adding additional acceptance criteria fields"""
        additional = ['customfield_12345', 'customfield_67890']
        config = FieldWhitelistConfig(additional_acceptance_criteria_fields=additional)

        # Additional fields should be added to safe_fields
        assert 'customfield_12345' in config.safe_fields
        assert 'customfield_67890' in config.safe_fields

    def test_is_field_allowed_safe_field(self):
        """Test that safe fields are allowed"""
        config = FieldWhitelistConfig()

        assert config.is_field_allowed('summary') is True
        assert config.is_field_allowed('description') is True
        assert config.is_field_allowed('priority') is True

    def test_is_field_allowed_blocked_field(self):
        """Test that blocked fields are rejected"""
        config = FieldWhitelistConfig()

        assert config.is_field_allowed('reporter') is False
        assert config.is_field_allowed('assignee') is False
        assert config.is_field_allowed('worklog') is False

    def test_is_field_allowed_blocked_priority_over_safe(self):
        """Test that blocked fields take priority over safe fields"""
        # Create config where a field is in both safe and blocked
        config = FieldWhitelistConfig(
            safe_fields={'summary', 'reporter'},
            blocked_fields={'reporter'}
        )

        # Blocked should take priority
        assert config.is_field_allowed('reporter') is False
        assert config.is_field_allowed('summary') is True

    def test_is_field_allowed_acceptance_criteria_heuristic(self):
        """Test that fields containing 'acceptance' or 'criteria' are allowed"""
        config = FieldWhitelistConfig()

        # Should match heuristic even if not in safe_fields
        assert config.is_field_allowed('customfield_acceptance') is True
        assert config.is_field_allowed('customfield_criteria') is True
        assert config.is_field_allowed('acceptance_criteria_field') is True

    def test_is_field_allowed_unknown_field_blocked(self):
        """Test that unknown fields are blocked by default"""
        config = FieldWhitelistConfig()

        assert config.is_field_allowed('unknown_custom_field') is False
        assert config.is_field_allowed('customfield_99999') is False


# ============================================================================
# CODE BLOCK REMOVAL TESTS
# ============================================================================

class TestRemoveCodeBlocks:
    """Tests for code block removal functionality"""

    def test_remove_markdown_code_blocks(self):
        """Test removal of markdown code blocks with backticks"""
        text = """
Some text before
```python
def secret_function():
    api_key = "secret123"
    return api_key
```
Some text after
"""
        result = remove_code_blocks(text)

        assert "[CODE_BLOCK_REMOVED]" in result
        assert "secret_function" not in result
        assert "api_key" not in result
        assert "Some text before" in result
        assert "Some text after" in result

    def test_remove_jira_code_blocks(self):
        """Test removal of Jira code blocks {code}...{code}"""
        text = """
Description here
{code:java}
String password = "myPassword123";
System.out.println(password);
{code}
More description
"""
        result = remove_code_blocks(text)

        assert "[CODE_BLOCK_REMOVED]" in result
        assert "password" not in result
        assert "myPassword123" not in result
        assert "Description here" in result
        assert "More description" in result

    def test_remove_inline_code(self):
        """Test removal of inline code with single backticks"""
        text = "Use the command `kubectl get secrets` to view secrets"
        result = remove_code_blocks(text)

        assert "[CODE_BLOCK_REMOVED]" in result
        assert "kubectl get secrets" not in result
        assert "Use the command" in result
        assert "to view secrets" in result

    def test_remove_sql_queries(self):
        """Test removal of SQL queries"""
        text = """
Query example:
SELECT password, credit_card FROM users WHERE id = 123;
End of query
"""
        result = remove_code_blocks(text)

        assert "[CODE_BLOCK_REMOVED]" in result
        assert "SELECT" not in result
        assert "password" not in result
        assert "Query example:" in result
        assert "End of query" in result

    def test_remove_multiple_code_blocks(self):
        """Test removal of multiple different code block types"""
        text = """
First section
```javascript
const token = "abc123xyz";
```
Middle section
{code}
api_key = "secret"
{code}
Last section with `inline code`
"""
        result = remove_code_blocks(text)

        # Should have 3 replacements
        assert result.count("[CODE_BLOCK_REMOVED]") == 3
        assert "token" not in result
        assert "api_key" not in result
        assert "inline code" not in result
        assert "First section" in result
        assert "Middle section" in result
        assert "Last section with" in result

    def test_custom_replacement_text(self):
        """Test using custom replacement text"""
        text = "```python\ncode here\n```"
        result = remove_code_blocks(text, replacement="[REDACTED]")

        assert "[REDACTED]" in result
        assert "[CODE_BLOCK_REMOVED]" not in result

    def test_empty_text(self):
        """Test handling of empty text"""
        assert remove_code_blocks("") == ""
        assert remove_code_blocks(None) is None

    def test_text_without_code_blocks(self):
        """Test that normal text is unchanged"""
        text = "This is normal text without any code blocks"
        result = remove_code_blocks(text)

        assert result == text

    def test_potential_api_keys_not_removed_by_default(self):
        """Test that potential API keys are NOT removed by default (to avoid false positives)"""
        # 32+ character alphanumeric string (potential API key)
        # Using generic pattern, not real API key format
        text = "The key is ABCD1234567890abcdefghijklmnopqrstuvwxyz123456 here"
        result = remove_code_blocks(text)

        # Key should still be in text (not removed by default to avoid false positives)
        assert "ABCD1234567890abcdefghijklmnopqrstuvwxyz123456" in result
        # Warning feature is optional, not testing it here


# ============================================================================
# JIRA TICKET SANITIZATION TESTS
# ============================================================================

class TestSanitizeJiraTicket:
    """Tests for Jira ticket sanitization"""

    def test_sanitize_basic_ticket(self):
        """Test sanitizing a basic ticket with safe fields"""
        ticket = {
            'key': 'PROJ-123',
            'id': '10001',
            'fields': {
                'summary': 'Implement login feature',
                'description': 'Add user authentication',
                'priority': {'name': 'High'},
                'status': {'name': 'In Progress'}
            }
        }

        result = sanitize_jira_ticket(ticket)

        assert result['key'] == 'PROJ-123'
        assert result['id'] == '10001'
        assert result['fields']['summary'] == 'Implement login feature'
        assert result['fields']['description'] == 'Add user authentication'
        assert result['fields']['priority'] == {'name': 'High'}

    def test_sanitize_removes_blocked_fields(self):
        """Test that blocked fields are removed"""
        ticket = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'Safe field',
                'reporter': {'name': 'john.doe'},  # Blocked
                'assignee': {'name': 'jane.smith'},  # Blocked
                'worklog': [{'author': 'user1'}],  # Blocked
                'comment': [{'body': 'Internal comment'}]  # Blocked
            }
        }

        result = sanitize_jira_ticket(ticket)

        # Safe field should be present
        assert 'summary' in result['fields']

        # Blocked fields should be removed
        assert 'reporter' not in result['fields']
        assert 'assignee' not in result['fields']
        assert 'worklog' not in result['fields']
        assert 'comment' not in result['fields']

    def test_sanitize_removes_code_from_description(self):
        """Test that code blocks are removed from text fields"""
        ticket = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'Test ticket',
                'description': '''
                Description with code:
                ```python
                secret = "abc123"
                ```
                End of description
                '''
            }
        }

        result = sanitize_jira_ticket(ticket)

        assert 'secret' not in result['fields']['description']
        assert '[CODE_BLOCK_REMOVED]' in result['fields']['description']
        assert 'Description with code:' in result['fields']['description']

    def test_sanitize_with_code_removal_disabled(self):
        """Test sanitization with code removal disabled"""
        ticket = {
            'key': 'PROJ-123',
            'fields': {
                'description': '```python\ncode here\n```'
            }
        }

        result = sanitize_jira_ticket(ticket, remove_code=False)

        # Code should NOT be removed
        assert '```python\ncode here\n```' in result['fields']['description']
        assert '[CODE_BLOCK_REMOVED]' not in result['fields']['description']

    def test_sanitize_preserves_structure_for_dict_fields(self):
        """Test that dictionary fields (like ADF) are preserved"""
        ticket = {
            'key': 'PROJ-123',
            'fields': {
                'description': {
                    'type': 'doc',
                    'content': [{'type': 'paragraph', 'text': 'ADF content'}]
                }
            }
        }

        result = sanitize_jira_ticket(ticket)

        # Should preserve the dict structure
        assert isinstance(result['fields']['description'], dict)
        assert result['fields']['description']['type'] == 'doc'

    def test_sanitize_handles_various_field_types(self):
        """Test handling of different field value types"""
        ticket = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'String field',  # str
                'priority': {'name': 'High'},  # dict
                'labels': ['bug', 'urgent'],  # list
                'customfield_10016': 5,  # int (story points)
                'timeestimate': 3600,  # int
                # Note: bool and None fields not tested because they may not be in SAFE_FIELDS by default
            }
        }

        result = sanitize_jira_ticket(ticket)

        assert result['fields']['summary'] == 'String field'
        assert result['fields']['priority'] == {'name': 'High'}
        assert result['fields']['labels'] == ['bug', 'urgent']
        assert result['fields']['customfield_10016'] == 5
        assert result['fields']['timeestimate'] == 3600

    def test_sanitize_with_custom_whitelist_config(self):
        """Test using custom whitelist configuration"""
        # Create custom config that only allows 'summary'
        config = FieldWhitelistConfig(
            safe_fields={'summary'},
            blocked_fields=set()
        )

        ticket = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'Allowed',
                'description': 'Not allowed with custom config',
                'priority': 'Not allowed'
            }
        }

        result = sanitize_jira_ticket(ticket, whitelist_config=config)

        assert 'summary' in result['fields']
        assert 'description' not in result['fields']
        assert 'priority' not in result['fields']

    def test_sanitize_unknown_type_skipped(self):
        """Test that unknown field types are skipped"""
        # Use a custom config that allows 'customfield_weird'
        config = FieldWhitelistConfig(
            safe_fields={'summary', 'customfield_weird'}
        )

        ticket = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'Normal field',
                'customfield_weird': object()  # Weird type
            }
        }

        result = sanitize_jira_ticket(ticket, whitelist_config=config)

        # Unknown type should be skipped (even though it's in safe_fields)
        assert 'customfield_weird' not in result['fields']
        # Summary should still be present
        assert 'summary' in result['fields']


# ============================================================================
# DESCRIPTION SANITIZATION TESTS
# ============================================================================

class TestSanitizeTicketDescription:
    """Tests for ticket description sanitization"""

    def test_sanitize_description_removes_code(self):
        """Test that code blocks are removed from description"""
        description = "Text before ```code\nsecret\n``` text after"
        result = sanitize_ticket_description(description)

        assert '[CODE_BLOCK_REMOVED]' in result
        assert 'secret' not in result

    def test_sanitize_description_no_code_removal(self):
        """Test description sanitization with code removal disabled"""
        description = "```code here```"
        result = sanitize_ticket_description(description, remove_code=False)

        assert '```code here```' == result

    def test_sanitize_empty_description(self):
        """Test handling of empty description"""
        assert sanitize_ticket_description("") == ""
        assert sanitize_ticket_description(None) is None


# ============================================================================
# DOCUMENT CONTENT SANITIZATION TESTS
# ============================================================================

class TestSanitizeDocumentContent:
    """Tests for document content sanitization"""

    def test_sanitize_document_removes_code(self):
        """Test that code blocks are removed from documents"""
        content = "Document with {code}secret code{code} in it"
        result = sanitize_document_content(content)

        assert '[CODE_BLOCK_REMOVED]' in result
        assert 'secret code' not in result

    def test_sanitize_document_no_code_removal(self):
        """Test document sanitization with code removal disabled"""
        content = "```code```"
        result = sanitize_document_content(content, remove_code=False)

        assert '```code```' == result

    def test_sanitize_empty_document(self):
        """Test handling of empty document content"""
        assert sanitize_document_content("") == ""
        assert sanitize_document_content(None) is None


# ============================================================================
# ATTACHMENT SANITIZATION TESTS
# ============================================================================

class TestSanitizeAttachment:
    """Tests for attachment sanitization"""

    def test_sanitize_document_attachment(self):
        """Test sanitizing a document attachment"""
        attachment = {
            'type': 'document',
            'filename': 'requirements.txt',
            'content': 'Requirements:\n```\nsecret config\n```\nEnd'
        }

        result = sanitize_attachment(attachment)

        assert result['type'] == 'document'
        assert result['filename'] == 'requirements.txt'
        assert '[CODE_BLOCK_REMOVED]' in result['content']
        assert 'secret config' not in result['content']

    def test_sanitize_image_attachment(self):
        """Test that image attachments are passed through (Phase 2 will handle OCR)"""
        attachment = {
            'type': 'image',
            'filename': 'screenshot.png',
            'data': 'base64encodeddata=='
        }

        result = sanitize_attachment(attachment)

        # Should be unchanged (images handled in Phase 2)
        assert result == attachment

    def test_sanitize_attachment_no_code_removal(self):
        """Test attachment sanitization with code removal disabled"""
        attachment = {
            'type': 'document',
            'content': '```code```'
        }

        result = sanitize_attachment(attachment, remove_code=False)

        assert '```code```' in result['content']

    def test_sanitize_attachment_without_content(self):
        """Test sanitizing attachment without content field"""
        attachment = {
            'type': 'unknown',
            'filename': 'file.xyz'
        }

        result = sanitize_attachment(attachment)

        # Should just copy the attachment
        assert result == attachment


# ============================================================================
# SANITIZATION SUMMARY TESTS
# ============================================================================

class TestGetSanitizationSummary:
    """Tests for sanitization summary generation"""

    def test_summary_counts_removed_fields(self):
        """Test that summary correctly counts removed fields"""
        original = {
            'fields': {
                'summary': 'Test',
                'description': 'Test desc',
                'reporter': 'user1',
                'assignee': 'user2',
                'worklog': []
            }
        }

        sanitized = {
            'fields': {
                'summary': 'Test',
                'description': 'Test desc'
            }
        }

        summary = get_sanitization_summary(original, sanitized)

        assert summary['total_fields'] == 5
        assert summary['safe_fields'] == 2
        assert summary['removed_fields'] == 3
        assert 'reporter' in summary['removed_field_names']
        assert 'assignee' in summary['removed_field_names']
        assert 'worklog' in summary['removed_field_names']

    def test_summary_no_fields_removed(self):
        """Test summary when no fields are removed"""
        original = {
            'fields': {
                'summary': 'Test',
                'description': 'Test'
            }
        }

        sanitized = {
            'fields': {
                'summary': 'Test',
                'description': 'Test'
            }
        }

        summary = get_sanitization_summary(original, sanitized)

        assert summary['total_fields'] == 2
        assert summary['safe_fields'] == 2
        assert summary['removed_fields'] == 0
        assert summary['removed_field_names'] == []

    def test_summary_all_fields_removed(self):
        """Test summary when all fields are removed"""
        original = {
            'fields': {
                'reporter': 'user1',
                'assignee': 'user2'
            }
        }

        sanitized = {
            'fields': {}
        }

        summary = get_sanitization_summary(original, sanitized)

        assert summary['total_fields'] == 2
        assert summary['safe_fields'] == 0
        assert summary['removed_fields'] == 2


# ============================================================================
# IMAGE SANITIZATION TESTS (PHASE 2.1)
# ============================================================================

class TestSanitizeImageAttachment:
    """Tests for sanitize_image_attachment function"""

    def test_image_blocked_with_maximum_security(self):
        """Test that images are completely blocked with maximum security level"""
        attachment = {
            "type": "image",
            "filename": "screenshot.png",
            "mime_type": "image/png",
            "content": "base64_encoded_image_data_here",
            "data_url": "data:image/png;base64,..."
        }

        result = sanitize_image_attachment(attachment, security_level="maximum")

        # Should be blocked
        assert result["type"] == "image_blocked"
        assert result["filename"] == "screenshot.png"
        assert result["original_type"] == "image"
        assert result["note"] == "[IMAGE BLOCKED FOR SECURITY]"
        assert "potential sensitive visual data" in result["message"]

        # Should not contain any image data
        assert "content" not in result
        assert "data_url" not in result

    def test_image_blocked_preserves_filename(self):
        """Test that filename is preserved when image is blocked"""
        attachment = {
            "type": "image",
            "filename": "architecture_diagram.jpg",
            "content": "image_data"
        }

        result = sanitize_image_attachment(attachment, security_level="maximum")

        assert result["filename"] == "architecture_diagram.jpg"
        assert result["type"] == "image_blocked"

    def test_image_blocked_handles_missing_filename(self):
        """Test that missing filename defaults to 'unknown.png'"""
        attachment = {
            "type": "image",
            "content": "image_data"
        }

        result = sanitize_image_attachment(attachment, security_level="maximum")

        assert result["filename"] == "unknown.png"
        assert result["type"] == "image_blocked"

    def test_image_blocked_message_explains_reason(self):
        """Test that blocked message explains why images are blocked"""
        attachment = {
            "type": "image",
            "filename": "mockup.png",
            "content": "image_data"
        }

        result = sanitize_image_attachment(attachment, security_level="maximum")

        message = result["message"]

        # Should mention various types of sensitive data
        assert "internal URLs" in message or "internal urls" in message.lower()
        assert "employee names" in message or "employee" in message.lower()
        assert "customer data" in message or "customer" in message.lower()
        assert "architecture diagrams" in message or "architecture" in message.lower()

        # Should mention security reason
        assert "security" in message.lower()
        assert "blocked" in message.lower()

    def test_unsupported_security_level_raises_error(self):
        """Test that unsupported security levels raise NotImplementedError"""
        attachment = {
            "type": "image",
            "filename": "test.png",
            "content": "image_data"
        }

        # These security levels are planned for future phases
        for level in ["high", "medium", "low"]:
            with pytest.raises(NotImplementedError) as exc_info:
                sanitize_image_attachment(attachment, security_level=level)

            assert level in str(exc_info.value)
            assert "not yet implemented" in str(exc_info.value).lower()
            assert "maximum" in str(exc_info.value).lower()

    def test_image_blocked_default_security_level(self):
        """Test that default security level is 'maximum'"""
        attachment = {
            "type": "image",
            "filename": "test.png",
            "content": "image_data"
        }

        # Call without specifying security_level
        result = sanitize_image_attachment(attachment)

        # Should default to maximum (blocked)
        assert result["type"] == "image_blocked"

    def test_image_blocked_removes_all_image_content(self):
        """Test that all image-related content is removed"""
        attachment = {
            "type": "image",
            "filename": "sensitive.png",
            "mime_type": "image/png",
            "content": "very_sensitive_base64_data",
            "data_url": "data:image/png;base64,very_sensitive_data",
            "size": 102400,
            "some_other_field": "value"
        }

        result = sanitize_image_attachment(attachment, security_level="maximum")

        # Should only have safe metadata fields
        assert "type" in result  # Changed to "image_blocked"
        assert "filename" in result
        assert "original_type" in result
        assert "note" in result
        assert "message" in result

        # Should NOT contain sensitive fields
        assert "content" not in result
        assert "data_url" not in result
        assert "size" not in result  # Size is not security-critical but not needed
        assert "some_other_field" not in result
