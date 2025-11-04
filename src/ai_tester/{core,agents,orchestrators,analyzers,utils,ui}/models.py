"""
Data models for AI Tester framework
Includes both Pydantic models for API and dataclasses for internal use
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import IntEnum

# Try to import Pydantic for structured outputs
try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object


# ========== PYDANTIC MODELS (For OpenAI Structured Outputs) ==========

if PYDANTIC_AVAILABLE:
    class TestStepSchema(BaseModel):
        """Schema for a test step."""
        action: str = Field(description="Clear, specific action to perform")
        expected: str = Field(description="Observable, verifiable expected result")
    
    
    class RequirementSchema(BaseModel):
        """Schema for a requirement."""
        id: str = Field(description="Unique ID like REQ-001, REQ-002")
        description: str = Field(description="Clear, testable requirement description")
        source: str = Field(description="Source: 'Acceptance Criteria', 'Description', or 'User Story'")
    
    
    class TestCaseSchema(BaseModel):
        """Schema for a test case."""
        requirement_id: str = Field(description="Links to requirement ID (e.g., REQ-001)")
        requirement_desc: str = Field(description="Brief summary of the requirement")
        title: str = Field(description="Clear, descriptive test case title")
        priority: Literal[1, 2, 3, 4] = Field(description="1=Critical, 2=High, 3=Medium, 4=Low")
        test_type: Literal["Positive", "Negative", "Edge Case"] = Field(description="Test type classification")
        tags: List[str] = Field(default_factory=list, description="Relevant tags for categorization")
        steps: List[TestStepSchema] = Field(description="3-8 detailed test steps covering complete user journey")
    
    
    class TestGenerationResponse(BaseModel):
        """Response from test generation."""
        requirements: List[RequirementSchema] = Field(description="All identified requirements from ticket")
        test_cases: List[TestCaseSchema] = Field(description="Exactly 3 test cases per requirement (1 Positive, 1 Negative, 1 Edge)")
    
    
    class TestCaseIssue(BaseModel):
        """An issue found in a test case."""
        test_case_title: str = Field(description="Title of the test case with the issue")
        requirement_id: str = Field(description="Associated requirement ID")
        issue_type: Literal["missing_steps", "incomplete_flow", "unclear_expected", "wrong_test_type", "missing_requirement", "insufficient_requirements", "over_consolidated_requirements", "duplicate", "priority_mismatch", "other"]
        severity: Literal["critical", "major", "minor"] = Field(description="Severity of the issue")
        description: str = Field(description="Clear description of what's wrong")
        suggestion: str = Field(description="Specific suggestion for how to fix it")
    
    
    class CriticReviewResponse(BaseModel):
        """Response from critic review."""
        overall_quality: Literal["excellent", "good", "needs_improvement", "poor"] = Field(description="Overall quality assessment")
        approved: bool = Field(description="True if test cases meet quality standards, False if refinement needed")
        confidence_score: int = Field(description="Confidence in assessment (0-100)", ge=0, le=100)
        
        requirement_count_correct: bool = Field(description="True if all requirements are properly identified")
        test_count_correct: bool = Field(description="True if exactly 3 test cases per requirement (formula: N×3)")
        test_type_distribution_correct: bool = Field(description="True if each requirement has 1 Positive, 1 Negative, 1 Edge")
        steps_complete: bool = Field(description="True if all test cases have 3-8 detailed steps")
        traceability_correct: bool = Field(description="True if all test cases properly link to requirements")
        
        strengths: List[str] = Field(description="What was done well (2-4 points)")
        issues_found: List[TestCaseIssue] = Field(description="Specific issues that need correction")
        missing_test_scenarios: List[str] = Field(description="Important scenarios that should be tested but aren't covered")
        
        summary: str = Field(description="2-3 sentence summary of the review")
        recommendation: str = Field(description="Clear recommendation: 'Approve' or specific actions needed")
    
    
    class TestTicketSplit(BaseModel):
        """Recommendation for splitting test tickets."""
        functional_area: str = Field(description="Name of the functional area (e.g., 'Fleet Data Migration')")
        child_tickets: List[str] = Field(description="Child ticket keys that relate to this area")
        estimated_ac_count: int = Field(description="Estimated number of acceptance criteria (5-8 recommended)")
        rationale: str = Field(description="Why these tickets are grouped together")
    
    
    class TestTicketSplitResponse(BaseModel):
        """Response for test ticket split recommendations."""
        recommended_splits: List[TestTicketSplit] = Field(description="Recommended test ticket structure")
        total_tickets: int = Field(description="Total number of test tickets to create")
        reasoning: str = Field(description="Overall strategy for splitting")
    
    
    class TestTicketContent(BaseModel):
        """Content for a test ticket."""
        summary: str = Field(description="Ticket summary following Epic naming convention")
        description: str = Field(description="Detailed description matching Epic's writing style")
        acceptance_criteria: List[str] = Field(description="5-8 black-box acceptance criteria for manual testing")
        quality_estimate: int = Field(description="Self-estimated quality score (0-100)", ge=0, le=100)
    
    
    class TestTicketReview(BaseModel):
        """Review of a test ticket."""
        approved: bool = Field(description="True if ticket is ready, False if needs revision")
        quality_score: int = Field(description="Quality assessment score (0-100)", ge=0, le=100)
        strengths: List[str] = Field(description="What was done well")
        issues: List[str] = Field(description="Problems that need fixing")
        recommendations: List[str] = Field(description="Specific improvements needed")
        revised_content: Optional[TestTicketContent] = Field(default=None, description="Revised ticket if approved=False")


# ========== DATACLASSES (For Internal Use) ==========

class Priority(IntEnum):
    """Test priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TestStep:
    """A single test step."""
    action: str
    expected: str
    number: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "action": self.action,
            "expected": self.expected,
            "number": self.number
        }


@dataclass
class Requirement:
    """A requirement to be tested."""
    id: str  # REQ-001, AC-001, etc.
    description: str
    source: str  # "Acceptance Criteria", "Description", "User Story", etc.
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "source": self.source
        }


@dataclass
class TestCase:
    """A complete test case."""
    title: str
    objective: str = ""
    priority: int = 2
    test_type: str = "Positive"  # Positive, Negative, or Edge Case
    tags: List[str] = field(default_factory=list)
    steps: List[TestStep] = field(default_factory=list)
    requirement_id: str = ""  # Links to Requirement.id
    requirement_desc: str = ""  # For display purposes
    
    def add_step(self, action: str, expected: str) -> 'TestCase':
        """Add a test step."""
        step_number = len(self.steps) + 1
        self.steps.append(TestStep(action=action, expected=expected, number=step_number))
        return self
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "objective": self.objective,
            "priority": self.priority,
            "test_type": self.test_type,
            "tags": self.tags,
            "steps": [step.to_dict() for step in self.steps],
            "requirement_id": self.requirement_id,
            "requirement_desc": self.requirement_desc
        }


@dataclass
class GeneratedTestTicket:
    """A generated test ticket with its state."""
    id: int
    title: str
    summary: str
    description: str
    acceptance_criteria: List[str]
    quality_score: int
    ac_count: int
    analyzed: bool = False
    test_cases: Optional[List[TestCase]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "quality_score": self.quality_score,
            "ac_count": self.ac_count,
            "analyzed": self.analyzed,
            "test_cases": [tc.to_dict() for tc in self.test_cases] if self.test_cases else None
        }


@dataclass
class EpicContext:
    """Context from a Jira Epic."""
    epic_key: str
    epic_summary: str
    epic_description: str
    child_issues: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "epic_key": self.epic_key,
            "epic_summary": self.epic_summary,
            "epic_description": self.epic_description,
            "child_issues": self.child_issues
        }