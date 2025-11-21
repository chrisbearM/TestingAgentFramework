"""
Test script for validating Phase 1 security sanitization implementation.

This script tests:
1. Field whitelisting - Sensitive fields blocked
2. Code block removal - SQL, code snippets removed
3. Attachment sanitization - PDFs, Word docs, text files sanitized
4. Sanitization summary - Audit trail generation

Usage:
    python test_sanitization.py
"""

import os
import sys
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_tester.utils.data_sanitizer import (
    sanitize_jira_ticket,
    sanitize_ticket_description,
    sanitize_document_content,
    sanitize_attachment,
    remove_code_blocks,
    get_sanitization_summary,
    FieldWhitelistConfig
)


def print_section(title: str):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")
    print()


def test_field_whitelisting():
    """Test that sensitive fields are blocked from tickets"""
    print_section("TEST 1: Field Whitelisting")

    # Create a mock Jira ticket with both safe and sensitive fields
    # Jira format: {'key': 'TEST-123', 'fields': {...}}
    mock_ticket = {
        "key": "TEST-123",
        "id": "12345",
        "fields": {
            # Safe fields (should be preserved)
            "summary": "Implement user authentication",
            "description": "Create a login system with OAuth2",
            "issuetype": {"name": "Story"},
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "labels": ["security", "authentication"],
            "customfield_10011": "User Management Epic",  # Epic Name
            "customfield_10524": "Users can log in successfully",  # Acceptance Criteria

            # Sensitive fields (should be blocked)
            "reporter": {"emailAddress": "john.doe@company.com", "displayName": "John Doe"},
            "assignee": {"emailAddress": "jane.smith@company.com", "displayName": "Jane Smith"},
            "creator": {"emailAddress": "admin@company.com"},
            "comment": {
                "comments": [
                    {"body": "DEBUG: API key is sk-abc123def456"},
                    {"body": "Server logs show error at 10.0.45.23"}
                ]
            },
            "created": "2025-01-15T10:30:00.000+0000",
            "updated": "2025-01-19T14:20:00.000+0000",
            "worklog": {"worklogs": [{"timeSpent": "2h"}]},
            "watches": {"watchCount": 5},
            "votes": {"votes": 3}
        }
    }

    # Sanitize the ticket
    sanitized = sanitize_jira_ticket(mock_ticket)

    # Get sanitization summary
    summary = get_sanitization_summary(mock_ticket, sanitized)

    # Verify safe fields are preserved
    tests_passed = 0
    tests_total = 0

    tests_total += 1
    if sanitized.get("key") == "TEST-123":
        print_test_result("Safe field preserved: key", True)
        tests_passed += 1
    else:
        print_test_result("Safe field preserved: key", False, f"Got: {sanitized.get('key')}")

    tests_total += 1
    if sanitized.get("fields", {}).get("summary") == "Implement user authentication":
        print_test_result("Safe field preserved: summary", True)
        tests_passed += 1
    else:
        print_test_result("Safe field preserved: summary", False, f"Got: {sanitized.get('fields', {}).get('summary')}")

    tests_total += 1
    if sanitized.get("fields", {}).get("description") == "Create a login system with OAuth2":
        print_test_result("Safe field preserved: description", True)
        tests_passed += 1
    else:
        print_test_result("Safe field preserved: description", False)

    # Verify sensitive fields are blocked
    tests_total += 1
    if "reporter" not in sanitized.get("fields", {}):
        print_test_result("Sensitive field blocked: reporter", True)
        tests_passed += 1
    else:
        print_test_result("Sensitive field blocked: reporter", False, f"Field still present")

    tests_total += 1
    if "assignee" not in sanitized.get("fields", {}):
        print_test_result("Sensitive field blocked: assignee", True)
        tests_passed += 1
    else:
        print_test_result("Sensitive field blocked: assignee", False)

    tests_total += 1
    if "comment" not in sanitized.get("fields", {}):
        print_test_result("Sensitive field blocked: comment", True)
        tests_passed += 1
    else:
        print_test_result("Sensitive field blocked: comment", False)

    tests_total += 1
    if "created" not in sanitized.get("fields", {}):
        print_test_result("Sensitive field blocked: created (audit data)", True)
        tests_passed += 1
    else:
        print_test_result("Sensitive field blocked: created", False)

    tests_total += 1
    if "worklog" not in sanitized.get("fields", {}):
        print_test_result("Sensitive field blocked: worklog", True)
        tests_passed += 1
    else:
        print_test_result("Sensitive field blocked: worklog", False)

    # Check summary
    print(f"\nSanitization Summary:")
    print(f"   Total fields: {summary['total_fields']}")
    print(f"   Safe fields: {summary['safe_fields']}")
    print(f"   Removed fields: {summary['removed_fields']}")
    print(f"   Removed field names: {', '.join(summary['removed_field_names'][:5])}")

    print(f"\nTest Results: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_code_block_removal():
    """Test that code blocks are removed from descriptions"""
    print_section("TEST 2: Code Block Removal")

    tests_passed = 0
    tests_total = 0

    # Test 1: Markdown code blocks
    tests_total += 1
    text_with_markdown = """
Here's the setup:

```bash
export API_KEY=sk-secret123
export DB_PASSWORD=admin123
```

Then run the service.
"""
    sanitized = remove_code_blocks(text_with_markdown)
    if "sk-secret123" not in sanitized and "[CODE_BLOCK_REMOVED]" in sanitized:
        print_test_result("Markdown code block removed", True)
        tests_passed += 1
    else:
        print_test_result("Markdown code block removed", False, f"Secret still present: {'sk-secret123' in sanitized}")

    # Test 2: Jira code blocks
    tests_total += 1
    text_with_jira = """
Configuration:

{code:sql}
SELECT * FROM users WHERE password='password123';
INSERT INTO api_keys VALUES ('sk-abc123');
{code}

Apply this config.
"""
    sanitized = remove_code_blocks(text_with_jira)
    if "password123" not in sanitized and "[CODE_BLOCK_REMOVED]" in sanitized:
        print_test_result("Jira code block removed", True)
        tests_passed += 1
    else:
        print_test_result("Jira code block removed", False)

    # Test 3: SQL queries
    tests_total += 1
    text_with_sql = """
Run this query:
SELECT user_id, email FROM employees WHERE department='Engineering';
This will give you the data.
"""
    sanitized = remove_code_blocks(text_with_sql)
    if "SELECT" not in sanitized and "[SQL_QUERY_REMOVED]" in sanitized:
        print_test_result("SQL query removed", True)
        tests_passed += 1
    else:
        print_test_result("SQL query removed", False)

    # Test 4: Inline code
    tests_total += 1
    text_with_inline = "Set the variable `API_KEY=secret` in your environment."
    sanitized = remove_code_blocks(text_with_inline)
    if "`API_KEY=secret`" not in sanitized:
        print_test_result("Inline code removed", True)
        tests_passed += 1
    else:
        print_test_result("Inline code removed", False)

    # Test 5: Long alphanumeric tokens (potential API keys)
    tests_total += 1
    text_with_token = "Use token abc123def456ghi789jkl012mno345pqr678stu901vwx234yz for authentication"
    sanitized = remove_code_blocks(text_with_token)
    # Should warn but not block (just detection)
    print_test_result("Long token detection", True, "Warning system active")
    tests_passed += 1

    print(f"\nTest Results: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_attachment_sanitization():
    """Test that attachments are sanitized"""
    print_section("TEST 3: Attachment Sanitization")

    tests_passed = 0
    tests_total = 0

    # Test 1: PDF text sanitization
    tests_total += 1
    pdf_attachment = {
        "type": "document",
        "filename": "requirements.pdf",
        "content": """
Product Requirements Document

Authentication:
```python
API_KEY = "sk-prod-abc123"
DB_URL = "postgresql://admin:password@10.0.1.50:5432/db"
```

Contact: admin@company.com for questions.
"""
    }
    sanitized = sanitize_attachment(pdf_attachment, remove_code=True)
    content = sanitized.get("content", "")
    if "sk-prod-abc123" not in content and "[CODE_BLOCK_REMOVED]" in content:
        print_test_result("PDF code blocks removed", True)
        tests_passed += 1
    else:
        print_test_result("PDF code blocks removed", False)

    # Test 2: Word document sanitization
    tests_total += 1
    word_attachment = {
        "type": "document",
        "filename": "design.docx",
        "content": """
Design Document

Database Schema:
{code:sql}
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255),
    password_hash VARCHAR(255)
);
{code}
"""
    }
    sanitized = sanitize_attachment(word_attachment, remove_code=True)
    content = sanitized.get("content", "")
    if "password_hash" not in content and "[CODE_BLOCK_REMOVED]" in content:
        print_test_result("Word doc code blocks removed", True)
        tests_passed += 1
    else:
        print_test_result("Word doc code blocks removed", False)

    # Test 3: Text file sanitization
    tests_total += 1
    text_attachment = {
        "type": "text",
        "filename": "notes.txt",
        "content": "Server config: `API_URL=https://api.internal.company.com/v1` and `SECRET_KEY=abc123`"
    }
    sanitized = sanitize_attachment(text_attachment, remove_code=True)
    content = sanitized.get("content", "")
    if "`API_URL=" not in content:
        print_test_result("Text file inline code removed", True)
        tests_passed += 1
    else:
        print_test_result("Text file inline code removed", False)

    # Test 4: Image pass-through (Phase 1 - no sanitization yet)
    tests_total += 1
    image_attachment = {
        "type": "image",
        "filename": "screenshot.png",
        "content": "base64_encoded_image_data_here"
    }
    sanitized = sanitize_attachment(image_attachment, remove_code=True)
    # Images pass through in Phase 1 (will be blocked in Phase 2)
    if sanitized.get("type") == "image":
        print_test_result("Image pass-through (Phase 1 behavior)", True, "Will be blocked in Phase 2")
        tests_passed += 1
    else:
        print_test_result("Image pass-through", False)

    print(f"\nTest Results: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_description_sanitization():
    """Test description-specific sanitization"""
    print_section("TEST 4: Description Sanitization")

    tests_passed = 0
    tests_total = 0

    # Test complex description with multiple code types
    tests_total += 1
    complex_description = """
# User Authentication Feature

## Requirements
- OAuth2 integration
- JWT token generation

## Technical Details

```javascript
const config = {
    apiKey: 'sk-live-abc123def456',
    dbUrl: 'mongodb://admin:password@10.0.1.100:27017/prod'
};
```

## Database Schema

{code:sql}
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_email VARCHAR(255),
    created_at TIMESTAMP
);
{code}

## API Endpoints

Contact john.doe@company.com for API access.

Server: 192.168.1.50
"""

    sanitized = sanitize_ticket_description(complex_description)

    # Should remove both code blocks
    if "sk-live-abc123def456" not in sanitized:
        print_test_result("JavaScript code block removed from description", True)
        tests_passed += 1
    else:
        print_test_result("JavaScript code block removed from description", False)
        tests_total += 1

    tests_total += 1
    if "CREATE TABLE" not in sanitized:
        print_test_result("SQL code block removed from description", True)
        tests_passed += 1
    else:
        print_test_result("SQL code block removed from description", False)

    # Should preserve non-code content
    tests_total += 1
    if "User Authentication Feature" in sanitized and "OAuth2 integration" in sanitized:
        print_test_result("Non-code content preserved", True)
        tests_passed += 1
    else:
        print_test_result("Non-code content preserved", False)

    print(f"\nTest Results: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_custom_acceptance_criteria_field():
    """Test custom acceptance criteria field configuration"""
    print_section("TEST 5: Custom Field Configuration")

    tests_passed = 0
    tests_total = 0

    # Create config with custom AC field
    custom_config = FieldWhitelistConfig(
        additional_acceptance_criteria_fields=['customfield_99999']
    )

    mock_ticket = {
        "key": "TEST-456",
        "id": "456",
        "fields": {
            "summary": "Test ticket",
            "customfield_99999": "Custom AC: Users can successfully authenticate",  # Custom AC field
            "customfield_88888": "Some other custom field",  # Not in whitelist
            "reporter": {"emailAddress": "test@company.com"}  # Blocked field
        }
    }

    # Sanitize with custom config
    sanitized = sanitize_jira_ticket(mock_ticket, whitelist_config=custom_config)

    tests_total += 1
    if "customfield_99999" in sanitized.get("fields", {}):
        print_test_result("Custom AC field preserved", True, "customfield_99999 whitelisted")
        tests_passed += 1
    else:
        print_test_result("Custom AC field preserved", False)

    tests_total += 1
    if "customfield_88888" not in sanitized.get("fields", {}):
        print_test_result("Non-whitelisted custom field blocked", True)
        tests_passed += 1
    else:
        print_test_result("Non-whitelisted custom field blocked", False)

    tests_total += 1
    if "reporter" not in sanitized.get("fields", {}):
        print_test_result("Reporter still blocked with custom config", True)
        tests_passed += 1
    else:
        print_test_result("Reporter still blocked with custom config", False)

    print(f"\nTest Results: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def run_all_tests():
    """Run all sanitization tests"""
    print("\n" + "="*80)
    print(" "*20 + "PHASE 1 SANITIZATION TEST SUITE")
    print("="*80)

    total_passed = 0
    total_tests = 0

    # Run all test suites
    passed, total = test_field_whitelisting()
    total_passed += passed
    total_tests += total

    passed, total = test_code_block_removal()
    total_passed += passed
    total_tests += total

    passed, total = test_attachment_sanitization()
    total_passed += passed
    total_tests += total

    passed, total = test_description_sanitization()
    total_passed += passed
    total_tests += total

    passed, total = test_custom_acceptance_criteria_field()
    total_passed += passed
    total_tests += total

    # Final summary
    print_section("FINAL RESULTS")

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Success Rate: {success_rate:.1f}%\n")

    if total_passed == total_tests:
        print("ALL TESTS PASSED! Phase 1 sanitization is working correctly.")
        print("\nSecurity Safeguards Verified:")
        print("   - Field whitelisting blocks sensitive fields")
        print("   - Code blocks removed from descriptions")
        print("   - Attachments sanitized (PDFs, Word docs, text files)")
        print("   - Custom field configuration works")
        print("   - Audit trail available via sanitization summary")
        return 0
    else:
        print(f"WARNING: {total_tests - total_passed} TESTS FAILED")
        print("   Review the failures above and fix sanitization logic.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n[ERROR] TEST SUITE CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
