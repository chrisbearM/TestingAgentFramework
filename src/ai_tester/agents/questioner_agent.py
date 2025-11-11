"""
Questioner Agent - Generates specific questions about Epic gaps and ambiguities

This agent analyzes the Epic and child tickets to identify:
- Missing information or unclear requirements
- Ambiguous acceptance criteria
- Technical gaps or unspecified details
- Edge cases not addressed
- Integration points not defined
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from .base_agent import BaseAgent


class QuestionerAgent(BaseAgent):
    """
    Generates targeted questions to clarify Epic requirements
    """

    def __init__(self, llm):
        super().__init__(llm)

    def generate_questions(
        self,
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]]
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Generate specific questions about gaps and ambiguities in the Epic

        Args:
            epic_data: Epic information (key, summary, description)
            child_tickets: List of child ticket data

        Returns:
            Tuple of (questions list, error message)
            Questions format:
            [
                {
                    "question": "What is the expected behavior when...",
                    "category": "Functional Requirements",
                    "related_tickets": ["TICKET-123"],
                    "rationale": "This is unclear because..."
                }
            ]
        """
        system_prompt = self._get_questioner_system_prompt()
        user_prompt = self._build_questioner_prompt(epic_data, child_tickets)

        result, error = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000
        )

        if error:
            return None, error

        # Parse JSON response
        questions_data = self._parse_json_response(result)
        if not questions_data or 'questions' not in questions_data:
            return None, "Failed to parse questions from response"

        return questions_data['questions'], None

    def _get_questioner_system_prompt(self) -> str:
        """System prompt for Questioner Agent"""
        return """You are an expert Business Analyst and Requirements Engineer.

Your role is to analyze Epics and their child tickets to identify gaps, ambiguities, and missing information.

Generate SPECIFIC, ACTIONABLE questions that will help clarify the requirements and ensure comprehensive test coverage.

Focus on:
1. **Functional Gaps**: Missing use cases, undefined behaviors, edge cases
2. **Technical Details**: Integration points, data formats, performance requirements
3. **Acceptance Criteria**: Vague or incomplete success criteria
4. **User Experience**: Unclear workflows, missing user personas
5. **Error Handling**: Unspecified error scenarios and validation rules
6. **Dependencies**: External systems, prerequisites, constraints

For each question:
- Be specific and reference concrete aspects of the Epic/tickets
- Explain WHY this information is needed (rationale)
- Categorize the question appropriately
- Link to related tickets if applicable

Categories:
- Functional Requirements
- Technical Specifications
- Acceptance Criteria
- User Experience
- Error Handling & Validation
- Integration & Dependencies
- Performance & Scalability
- Security & Compliance

Return ONLY valid JSON in this exact format:
{
  "questions": [
    {
      "question": "Specific question here?",
      "category": "Category name",
      "related_tickets": ["TICKET-123"],
      "rationale": "Why this question matters"
    }
  ]
}"""

    def _build_questioner_prompt(
        self,
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]]
    ) -> str:
        """Build the user prompt for question generation"""

        # Format child tickets
        tickets_text = ""
        for ticket in child_tickets[:20]:  # Limit to avoid token overflow
            tickets_text += f"\n- {ticket.get('key', 'N/A')}: {ticket.get('summary', 'N/A')}\n"
            if ticket.get('description'):
                # Truncate long descriptions
                desc = ticket['description'][:300]
                tickets_text += f"  Description: {desc}...\n"

        prompt = f"""Analyze the following Epic and generate specific questions to clarify gaps and ambiguities:

**Epic**: {epic_data.get('key', 'N/A')}
**Summary**: {epic_data.get('summary', 'N/A')}

**Description**:
{epic_data.get('description', 'No description provided')}

**Child Tickets** ({len(child_tickets)} total):
{tickets_text}

Generate 5-10 targeted questions that would help clarify requirements and ensure comprehensive test coverage.

Focus on:
- What is unclear or ambiguous?
- What edge cases are not addressed?
- What integration points are undefined?
- What acceptance criteria are missing?
- What error scenarios are not specified?

Return ONLY the JSON response with your questions."""

        return prompt
