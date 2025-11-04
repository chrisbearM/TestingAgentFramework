"""
Unit tests for core data models.

These tests demonstrate TDD approach and provide examples for writing
more tests as we build out the framework.
"""
import pytest
from ai_tester.core.models import (
    TestStep,
    Requirement,
    TestCase,
    GeneratedTestTicket,
    EpicContext,
    Priority
)


class TestTestStep:
    """Tests for TestStep model"""
    
    def test_create_test_step(self):
        """Test creating a basic test step"""
        step = TestStep(action="Click login button", expected="Login form appears")
        
        assert step.action == "Click login button"
        assert step.expected == "Login form appears"
        assert step.step_number is None
    
    def test_create_test_step_with_number(self):
        """Test creating a test step with explicit number"""
        step = TestStep(
            action="Enter username",
            expected="Username is accepted",
            step_number=1
        )
        
        assert step.step_number == 1
    
    def test_test_step_validation_empty_action(self):
        """Test that empty action raises ValueError"""
        with pytest.raises(ValueError, match="action cannot be empty"):
            TestStep(action="", expected="Something happens")
    
    def test_test_step_validation_empty_expected(self):
        """Test that empty expected raises ValueError"""
        with pytest.raises(ValueError, match="expected result cannot be empty"):
            TestStep(action="Do something", expected="")
    
    def test_test_step_validation_whitespace_only(self):
        """Test that whitespace-only strings are rejected"""
        with pytest.raises(ValueError):
            TestStep(action="   ", expected="Result")
        
        with pytest.raises(ValueError):
            TestStep(action="Action", expected="   ")
    
    def test_test_step_to_dict(self):
        """Test converting test step to dictionary"""
        step = TestStep(action="Click button", expected="Page loads", step_number=1)
        result = step.to_dict()
        
        assert result == {
            "step_number": 1,
            "action": "Click button",
            "expected": "Page loads"
        }


class TestRequirement:
    """Tests for Requirement model"""
    
    def test_create_requirement(self):
        """Test creating a basic requirement"""
        req = Requirement(req_id="REQ-1", text="User must be able to login")
        
        assert req.req_id == "REQ-1"
        assert req.text == "User must be able to login"
        assert req.priority == Priority.MEDIUM
    
    def test_create_requirement_with_priority(self):
        """Test creating requirement with specific priority"""
        req = Requirement(
            req_id="REQ-2",
            text="Critical security requirement",
            priority=Priority.HIGH
        )
        
        assert req.priority == Priority.HIGH
    
    def test_requirement_validation_empty_id(self):
        """Test that empty ID raises ValueError"""
        with pytest.raises(ValueError, match="ID cannot be empty"):
            Requirement(req_id="", text="Some text")
    
    def test_requirement_validation_empty_text(self):
        """Test that empty text raises ValueError"""
        with pytest.raises(ValueError, match="text cannot be empty"):
            Requirement(req_id="REQ-1", text="")
    
    def test_requirement_to_dict(self):
        """Test converting requirement to dictionary"""
        req = Requirement(req_id="REQ-1", text="Login required", priority=Priority.HIGH)
        result = req.to_dict()
        
        assert result == {
            "req_id": "REQ-1",
            "text": "Login required",
            "priority": "High"
        }


class TestTestCase:
    """Tests for TestCase model"""
    
    def test_create_test_case(self):
        """Test creating a basic test case"""
        tc = TestCase(id="TC-1", title="Test user login")
        
        assert tc.id == "TC-1"
        assert tc.title == "Test user login"
        assert len(tc.steps) == 0
        assert len(tc.requirements) == 0
        assert tc.priority == Priority.MEDIUM
    
    def test_create_test_case_with_steps(self):
        """Test creating test case with initial steps"""
        steps = [
            TestStep(action="Open page", expected="Page loads"),
            TestStep(action="Click login", expected="Form appears")
        ]
        tc = TestCase(id="TC-1", title="Login test", steps=steps)
        
        assert len(tc.steps) == 2
        assert tc.steps[0].step_number == 1
        assert tc.steps[1].step_number == 2
    
    def test_test_case_validation_empty_id(self):
        """Test that empty ID raises ValueError"""
        with pytest.raises(ValueError, match="ID cannot be empty"):
            TestCase(id="", title="Some title")
    
    def test_test_case_validation_empty_title(self):
        """Test that empty title raises ValueError"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            TestCase(id="TC-1", title="")
    
    def test_add_step(self):
        """Test adding steps to test case"""
        tc = TestCase(id="TC-1", title="Test")
        
        tc.add_step(TestStep(action="Step 1", expected="Result 1"))
        tc.add_step(TestStep(action="Step 2", expected="Result 2"))
        
        assert len(tc.steps) == 2
        assert tc.steps[0].step_number == 1
        assert tc.steps[1].step_number == 2
    
    def test_add_step_preserves_explicit_number(self):
        """Test that explicitly set step numbers are preserved"""
        tc = TestCase(id="TC-1", title="Test")
        
        tc.add_step(TestStep(action="Step", expected="Result", step_number=5))
        
        assert tc.steps[0].step_number == 5
    
    def test_add_requirement(self):
        """Test adding requirements to test case"""
        tc = TestCase(id="TC-1", title="Test")
        
        tc.add_requirement(Requirement(req_id="REQ-1", text="Login required"))
        tc.add_requirement(Requirement(req_id="REQ-2", text="Security check"))
        
        assert len(tc.requirements) == 2
        assert tc.requirements[0].req_id == "REQ-1"
    
    def test_add_tag(self):
        """Test adding tags to test case"""
        tc = TestCase(id="TC-1", title="Test")
        
        tc.add_tag("smoke-test")
        tc.add_tag("regression")
        
        assert len(tc.tags) == 2
        assert "smoke-test" in tc.tags
    
    def test_add_duplicate_tag(self):
        """Test that duplicate tags are not added"""
        tc = TestCase(id="TC-1", title="Test")
        
        tc.add_tag("smoke-test")
        tc.add_tag("smoke-test")
        
        assert len(tc.tags) == 1
    
    def test_add_empty_tag(self):
        """Test that empty tags are not added"""
        tc = TestCase(id="TC-1", title="Test")
        
        tc.add_tag("")
        tc.add_tag("   ")
        
        assert len(tc.tags) == 0
    
    def test_get_step_count(self):
        """Test getting step count"""
        tc = TestCase(id="TC-1", title="Test")
        assert tc.get_step_count() == 0
        
        tc.add_step(TestStep(action="Step 1", expected="Result 1"))
        assert tc.get_step_count() == 1
        
        tc.add_step(TestStep(action="Step 2", expected="Result 2"))
        assert tc.get_step_count() == 2
    
    def test_to_dict(self):
        """Test converting test case to dictionary"""
        tc = TestCase(id="TC-1", title="Login test", priority=Priority.HIGH)
        tc.add_step(TestStep(action="Open page", expected="Page loads"))
        tc.add_requirement(Requirement(req_id="REQ-1", text="Security"))
        tc.add_tag("smoke-test")
        tc.preconditions = "User not logged in"
        
        result = tc.to_dict()
        
        assert result["id"] == "TC-1"
        assert result["title"] == "Login test"
        assert result["priority"] == "High"
        assert len(result["steps"]) == 1
        assert len(result["requirements"]) == 1
        assert "smoke-test" in result["tags"]
        assert result["preconditions"] == "User not logged in"


class TestGeneratedTestTicket:
    """Tests for GeneratedTestTicket model"""
    
    def test_create_test_ticket(self):
        """Test creating a basic test ticket"""
        ticket = GeneratedTestTicket(
            title="User Authentication Tests",
            description="Tests for login and signup"
        )
        
        assert ticket.title == "User Authentication Tests"
        assert ticket.description == "Tests for login and signup"
        assert len(ticket.test_cases) == 0
        assert ticket.priority == Priority.MEDIUM
    
    def test_test_ticket_validation_empty_title(self):
        """Test that empty title raises ValueError"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            GeneratedTestTicket(title="", description="Description")
    
    def test_add_test_case(self):
        """Test adding test cases to ticket"""
        ticket = GeneratedTestTicket(title="Tests", description="Desc")
        
        tc1 = TestCase(id="TC-1", title="Test 1")
        tc2 = TestCase(id="TC-2", title="Test 2")
        
        ticket.add_test_case(tc1)
        ticket.add_test_case(tc2)
        
        assert len(ticket.test_cases) == 2
        assert ticket.test_cases[0].id == "TC-1"
    
    def test_get_test_case_count(self):
        """Test getting test case count"""
        ticket = GeneratedTestTicket(title="Tests", description="Desc")
        assert ticket.get_test_case_count() == 0
        
        ticket.add_test_case(TestCase(id="TC-1", title="Test 1"))
        assert ticket.get_test_case_count() == 1
    
    def test_get_total_step_count(self):
        """Test getting total step count across all test cases"""
        ticket = GeneratedTestTicket(title="Tests", description="Desc")
        
        tc1 = TestCase(id="TC-1", title="Test 1")
        tc1.add_step(TestStep(action="Step 1", expected="Result 1"))
        tc1.add_step(TestStep(action="Step 2", expected="Result 2"))
        
        tc2 = TestCase(id="TC-2", title="Test 2")
        tc2.add_step(TestStep(action="Step 3", expected="Result 3"))
        
        ticket.add_test_case(tc1)
        ticket.add_test_case(tc2)
        
        assert ticket.get_total_step_count() == 3
    
    def test_to_dict(self):
        """Test converting test ticket to dictionary"""
        ticket = GeneratedTestTicket(
            title="Auth Tests",
            description="Authentication testing",
            epic_key="EPIC-1",
            story_keys=["STORY-1", "STORY-2"],
            priority=Priority.HIGH
        )
        
        tc = TestCase(id="TC-1", title="Login test")
        tc.add_step(TestStep(action="Login", expected="Success"))
        ticket.add_test_case(tc)
        
        result = ticket.to_dict()
        
        assert result["title"] == "Auth Tests"
        assert result["epic_key"] == "EPIC-1"
        assert result["story_keys"] == ["STORY-1", "STORY-2"]
        assert result["priority"] == "High"
        assert len(result["test_cases"]) == 1
        assert result["stats"]["test_case_count"] == 1
        assert result["stats"]["total_step_count"] == 1


class TestEpicContext:
    """Tests for EpicContext model"""
    
    def test_create_epic_context(self):
        """Test creating an epic context"""
        epic = EpicContext(
            epic_key="EPIC-123",
            epic_summary="User Authentication",
            epic_description="Implement auth system"
        )
        
        assert epic.epic_key == "EPIC-123"
        assert epic.epic_summary == "User Authentication"
        assert len(epic.child_tickets) == 0
    
    def test_epic_context_validation_empty_key(self):
        """Test that empty epic key raises ValueError"""
        with pytest.raises(ValueError, match="Epic key cannot be empty"):
            EpicContext(
                epic_key="",
                epic_summary="Summary",
                epic_description="Description"
            )
    
    def test_get_child_count(self):
        """Test getting child ticket count"""
        epic = EpicContext(
            epic_key="EPIC-1",
            epic_summary="Summary",
            epic_description="Description",
            child_tickets=[
                {"key": "STORY-1", "summary": "Story 1"},
                {"key": "STORY-2", "summary": "Story 2"}
            ]
        )
        
        assert epic.get_child_count() == 2
    
    def test_get_child_keys(self):
        """Test getting list of child ticket keys"""
        epic = EpicContext(
            epic_key="EPIC-1",
            epic_summary="Summary",
            epic_description="Description",
            child_tickets=[
                {"key": "STORY-1", "summary": "Story 1"},
                {"key": "STORY-2", "summary": "Story 2"}
            ]
        )
        
        keys = epic.get_child_keys()
        assert keys == ["STORY-1", "STORY-2"]
    
    def test_get_child_keys_empty(self):
        """Test getting child keys when no children"""
        epic = EpicContext(
            epic_key="EPIC-1",
            epic_summary="Summary",
            epic_description="Description"
        )
        
        assert epic.get_child_keys() == []
    
    def test_to_dict(self):
        """Test converting epic context to dictionary"""
        epic = EpicContext(
            epic_key="EPIC-1",
            epic_summary="Auth System",
            epic_description="Build authentication",
            child_tickets=[{"key": "STORY-1"}],
            attachments=[{"filename": "design.pdf"}]
        )
        
        result = epic.to_dict()
        
        assert result["epic_key"] == "EPIC-1"
        assert result["epic_summary"] == "Auth System"
        assert len(result["child_tickets"]) == 1
        assert len(result["attachments"]) == 1
        assert result["stats"]["child_count"] == 1


# Integration-style tests combining multiple models
class TestModelIntegration:
    """Tests for models working together"""
    
    def test_complete_test_case_creation(self):
        """Test creating a complete test case with all components"""
        # Create test case
        tc = TestCase(
            id="TC-LOGIN-001",
            title="Verify successful user login",
            priority=Priority.HIGH,
            preconditions="User account exists with valid credentials"
        )
        
        # Add steps
        tc.add_step(TestStep(
            action="Navigate to login page",
            expected="Login form is displayed"
        ))
        tc.add_step(TestStep(
            action="Enter valid username and password",
            expected="Credentials are accepted"
        ))
        tc.add_step(TestStep(
            action="Click Login button",
            expected="User is redirected to dashboard"
        ))
        
        # Add requirements
        tc.add_requirement(Requirement(
            req_id="REQ-AUTH-001",
            text="System must authenticate users with valid credentials",
            priority=Priority.HIGH
        ))
        
        # Add tags
        tc.add_tag("smoke-test")
        tc.add_tag("authentication")
        
        # Verify complete structure
        assert tc.get_step_count() == 3
        assert len(tc.requirements) == 1
        assert len(tc.tags) == 2
        
        # Verify serialization
        result = tc.to_dict()
        assert result["id"] == "TC-LOGIN-001"
        assert len(result["steps"]) == 3
        assert result["steps"][0]["step_number"] == 1
    
    def test_complete_test_ticket_with_multiple_cases(self):
        """Test creating a complete test ticket with multiple test cases"""
        ticket = GeneratedTestTicket(
            title="User Authentication Test Suite",
            description="Comprehensive tests for login, logout, and password reset",
            epic_key="EPIC-AUTH-100",
            priority=Priority.HIGH
        )
        
        # Create first test case
        tc1 = TestCase(id="TC-1", title="Test successful login")
        tc1.add_step(TestStep(action="Login with valid creds", expected="Success"))
        
        # Create second test case
        tc2 = TestCase(id="TC-2", title="Test failed login")
        tc2.add_step(TestStep(action="Login with invalid creds", expected="Error shown"))
        
        # Add to ticket
        ticket.add_test_case(tc1)
        ticket.add_test_case(tc2)
        
        # Verify structure
        assert ticket.get_test_case_count() == 2
        assert ticket.get_total_step_count() == 2
        
        # Verify serialization
        result = ticket.to_dict()
        assert len(result["test_cases"]) == 2
        assert result["stats"]["test_case_count"] == 2
