"""
Data models for Test Ticket generation.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class TestTicket:
    """Represents a generated test ticket"""
    id: str
    summary: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    quality_score: Optional[int] = None
    review_feedback: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    epic_key: Optional[str] = None
    child_tickets: List[Dict[str, str]] = field(default_factory=list)  # [{key, summary}]
    functional_area: Optional[str] = None
    analyzed: bool = False
    test_cases: Optional[List[Dict[str, Any]]] = None
    requirements: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None
    selected_option_index: Optional[int] = None
    strategic_option: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Set created_at if not provided"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "quality_score": self.quality_score,
            "review_feedback": self.review_feedback,
            "raw_response": self.raw_response,
            "epic_key": self.epic_key,
            "child_tickets": self.child_tickets,
            "functional_area": self.functional_area,
            "analyzed": self.analyzed,
            "test_cases": self.test_cases,
            "requirements": self.requirements,
            "created_at": self.created_at,
            "selected_option_index": self.selected_option_index,
            "strategic_option": self.strategic_option,
            "stats": {
                "ac_count": len(self.acceptance_criteria),
                "test_case_count": len(self.test_cases) if self.test_cases else 0
            }
        }
