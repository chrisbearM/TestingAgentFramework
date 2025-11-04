"""
Core data models for AI Tester.

Extracted from original monolithic code and refactored for testability.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Priority(Enum):
    """Test priority levels"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class TestStep:
    """Represents a single test step"""
    action: str
    expected: str
    step_number: Optional[int] = None
    
    def __post_init__(self):
        """Validate step data"""
        if not self.action or not self.action.strip():
            raise ValueError("Test step action cannot be empty")
        if not self.expected or not self.expected.strip():
            raise ValueError("Test step expected result cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "step_number": self.step_number,
            "action": self.action,
            "expected": self.expected
        }


@dataclass
class Requirement:
    """Represents a requirement or acceptance criterion"""
    req_id: str
    text: str
    priority: Priority = Priority.MEDIUM
    
    def __post_init__(self):
        """Validate requirement data"""
        if not self.req_id or not self.req_id.strip():
            raise ValueError("Requirement ID cannot be empty")
        if not self.text or not self.text.strip():
            raise ValueError("Requirement text cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "req_id": self.req_id,
            "text": self.text,
            "priority": self.priority.value
        }


@dataclass
class TestCase:
    """Represents a complete test case"""
    id: str
    title: str
    steps: List[TestStep] = field(default_factory=list)
    requirements: List[Requirement] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    tags: List[str] = field(default_factory=list)
    preconditions: str = ""
    notes: str = ""
    
    def __post_init__(self):
        """Validate test case data"""
        if not self.id or not self.id.strip():
            raise ValueError("Test case ID cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("Test case title cannot be empty")
        
        # Assign step numbers if not set
        for i, step in enumerate(self.steps, 1):
            if step.step_number is None:
                step.step_number = i
    
    def add_step(self, step: TestStep) -> None:
        """Add a test step"""
        if step.step_number is None:
            step.step_number = len(self.steps) + 1
        self.steps.append(step)
    
    def add_requirement(self, requirement: Requirement) -> None:
        """Add a requirement"""
        self.requirements.append(requirement)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag"""
        if tag and tag.strip() and tag not in self.tags:
            self.tags.append(tag)
    
    def get_step_count(self) -> int:
        """Get number of steps"""
        return len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority.value,
            "steps": [step.to_dict() for step in self.steps],
            "requirements": [req.to_dict() for req in self.requirements],
            "tags": self.tags,
            "preconditions": self.preconditions,
            "notes": self.notes
        }


@dataclass
class GeneratedTestTicket:
    """Represents a generated test ticket (group of test cases)"""
    title: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    epic_key: Optional[str] = None
    story_keys: List[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    
    def __post_init__(self):
        """Validate ticket data"""
        if not self.title or not self.title.strip():
            raise ValueError("Test ticket title cannot be empty")
    
    def add_test_case(self, test_case: TestCase) -> None:
        """Add a test case to this ticket"""
        self.test_cases.append(test_case)
    
    def get_test_case_count(self) -> int:
        """Get number of test cases"""
        return len(self.test_cases)
    
    def get_total_step_count(self) -> int:
        """Get total number of steps across all test cases"""
        return sum(tc.get_step_count() for tc in self.test_cases)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "description": self.description,
            "epic_key": self.epic_key,
            "story_keys": self.story_keys,
            "priority": self.priority.value,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "stats": {
                "test_case_count": self.get_test_case_count(),
                "total_step_count": self.get_total_step_count()
            }
        }


@dataclass
class EpicContext:
    """Represents the context of an Epic with all its children"""
    epic_key: str
    epic_summary: str
    epic_description: str
    child_tickets: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate epic context"""
        if not self.epic_key or not self.epic_key.strip():
            raise ValueError("Epic key cannot be empty")
    
    def get_child_count(self) -> int:
        """Get number of child tickets"""
        return len(self.child_tickets)
    
    def get_child_keys(self) -> List[str]:
        """Get list of child ticket keys"""
        return [child.get("key", "") for child in self.child_tickets if child.get("key")]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "epic_key": self.epic_key,
            "epic_summary": self.epic_summary,
            "epic_description": self.epic_description,
            "child_tickets": self.child_tickets,
            "attachments": self.attachments,
            "stats": {
                "child_count": self.get_child_count()
            }
        }
