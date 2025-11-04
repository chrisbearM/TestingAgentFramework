"""
Pytest configuration and shared fixtures.

This file is automatically discovered by pytest and provides
fixtures that can be used across all test files.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock

from ai_tester.core.models import (
    TestStep,
    Requirement,
    TestCase,
    GeneratedTestTicket,
    EpicContext,
    Priority
)


# ===== Test Data Fixtures =====

@pytest.fixture
def sample_test_step():
    """Fixture providing a sample test step"""
    return TestStep(
        action="Click the login button",
        expected="Login form is displayed",
        step_number=1
    )


@pytest.fixture
def sample_requirement():
    """Fixture providing a sample requirement"""
    return Requirement(
        req_id="REQ-001",
        text="User must be able to login with valid credentials",
        priority=Priority.HIGH
    )


@pytest.fixture
def sample_test_case():
    """Fixture providing a sample test case with steps"""
    tc = TestCase(
        id="TC-LOGIN-001",
        title="Verify user login functionality",
        priority=Priority.HIGH,
        preconditions="User has valid credentials"
    )
    
    tc.add_step(TestStep(
        action="Navigate to login page",
        expected="Login form is displayed"
    ))
    tc.add_step(TestStep(
        action="Enter username and password",
        expected="Credentials are accepted"
    ))
    tc.add_step(TestStep(
        action="Click Login button",
        expected="User is logged in successfully"
    ))
    
    tc.add_requirement(Requirement(
        req_id="REQ-AUTH-001",
        text="System must authenticate valid users"
    ))
    
    tc.add_tag("smoke-test")
    tc.add_tag("authentication")
    
    return tc


@pytest.fixture
def sample_test_ticket():
    """Fixture providing a sample test ticket with multiple test cases"""
    ticket = GeneratedTestTicket(
        title="Authentication Test Suite",
        description="Tests for user authentication features",
        epic_key="EPIC-100",
        story_keys=["STORY-101", "STORY-102"],
        priority=Priority.HIGH
    )
    
    # Add first test case
    tc1 = TestCase(id="TC-1", title="Test successful login")
    tc1.add_step(TestStep(action="Login with valid creds", expected="Success"))
    ticket.add_test_case(tc1)
    
    # Add second test case
    tc2 = TestCase(id="TC-2", title="Test login failure")
    tc2.add_step(TestStep(action="Login with invalid creds", expected="Error shown"))
    ticket.add_test_case(tc2)
    
    return ticket


@pytest.fixture
def sample_epic_context():
    """Fixture providing a sample epic context"""
    return EpicContext(
        epic_key="EPIC-100",
        epic_summary="User Authentication System",
        epic_description="Implement complete user authentication with login, signup, and password reset",
        child_tickets=[
            {
                "key": "STORY-101",
                "summary": "Implement login page",
                "description": "Create login form with username and password fields"
            },
            {
                "key": "STORY-102",
                "summary": "Implement signup page",
                "description": "Create registration form for new users"
            },
            {
                "key": "STORY-103",
                "summary": "Implement password reset",
                "description": "Allow users to reset forgotten passwords"
            }
        ],
        attachments=[
            {
                "filename": "auth_mockup.png",
                "content_type": "image/png"
            }
        ]
    )


# ===== Mock Fixtures =====

@pytest.fixture
def mock_llm_client():
    """Fixture providing a mocked LLM client"""
    mock = Mock()
    mock.call.return_value = '{"result": "success"}'
    return mock


@pytest.fixture
def mock_jira_client():
    """Fixture providing a mocked Jira client"""
    mock = Mock()
    mock.fetch_epic.return_value = {
        "key": "EPIC-100",
        "fields": {
            "summary": "Test Epic",
            "description": "Test Description"
        }
    }
    return mock


# ===== File-based Fixtures =====

@pytest.fixture
def fixtures_dir():
    """Fixture providing path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_epic_json(fixtures_dir):
    """Fixture providing sample epic data from JSON file"""
    # For now, return inline data
    # Once we create the fixtures directory with JSON files, this will load from file
    return {
        "key": "EPIC-123",
        "fields": {
            "summary": "User Authentication System",
            "description": "Implement complete authentication",
            "subtasks": [
                {
                    "key": "STORY-1",
                    "fields": {
                        "summary": "Login page",
                        "description": "Create login interface"
                    }
                }
            ]
        }
    }


# ===== Configuration Fixtures =====

@pytest.fixture
def test_config():
    """Fixture providing test configuration"""
    return {
        "jira_base_url": "https://test.atlassian.net",
        "openai_model": "gpt-4",
        "max_retries": 3,
        "timeout": 30
    }


# ===== Pytest Configuration =====

def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (slower, may use real APIs)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests that take more than 1 second"
    )
    config.addinivalue_line(
        "markers",
        "requires_api_key: Tests that require API keys (OpenAI, Jira)"
    )


# ===== Helper Functions for Tests =====

@pytest.fixture
def assert_valid_test_case():
    """Fixture providing a helper function to validate test cases"""
    def _validator(test_case: TestCase):
        """Validate that a test case has all required fields"""
        assert test_case.id, "Test case must have an ID"
        assert test_case.title, "Test case must have a title"
        assert len(test_case.steps) > 0, "Test case must have at least one step"
        
        for i, step in enumerate(test_case.steps, 1):
            assert step.action, f"Step {i} must have an action"
            assert step.expected, f"Step {i} must have an expected result"
        
        return True
    
    return _validator


@pytest.fixture
def create_test_case_factory():
    """Fixture providing a factory function to create test cases"""
    def _factory(
        id_prefix="TC",
        title_prefix="Test Case",
        num_steps=3,
        priority=Priority.MEDIUM
    ):
        """Factory function to create test cases for testing"""
        tc = TestCase(
            id=f"{id_prefix}-{id(tc)}",  # Use object id for uniqueness
            title=f"{title_prefix} {id(tc)}",
            priority=priority
        )
        
        for i in range(1, num_steps + 1):
            tc.add_step(TestStep(
                action=f"Perform action {i}",
                expected=f"Expected result {i}"
            ))
        
        return tc
    
    return _factory
