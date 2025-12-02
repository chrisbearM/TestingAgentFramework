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
from pydantic import BaseModel, Field
from .base_agent import BaseAgent
from ai_tester.utils.jira_text_cleaner import sanitize_prompt_input


# Pydantic models for structured output
class Question(BaseModel):
    """Schema for a single question"""
    question: str = Field(description="Specific question to clarify requirements")
    category: str = Field(description="Category: Functional Requirements, Technical Specifications, Acceptance Criteria, User Experience, Error Handling & Validation, Integration & Dependencies, Performance & Scalability, or Security & Compliance")
    related_tickets: List[str] = Field(description="List of related ticket keys", default_factory=list)
    rationale: str = Field(description="Why this question matters and what information is missing")


class QuestionerResponse(BaseModel):
    """Complete response schema for question generation"""
    questions: List[Question] = Field(description="List of questions about gaps and ambiguities in the Epic")


class QuestionerAgent(BaseAgent):
    """
    Generates targeted questions to clarify Epic requirements
    """

    def __init__(self, llm):
        super().__init__(llm)

    def generate_questions(
        self,
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]],
        use_structured_output: bool = True
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Generate specific questions about gaps and ambiguities in the Epic

        Args:
            epic_data: Epic information (key, summary, description)
            child_tickets: List of child ticket data
            use_structured_output: Whether to use OpenAI structured outputs (default: True)

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

        if use_structured_output:
            result, error = self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000
            )

            if error:
                return None, error

            return result.get('questions', []), None
        else:
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
}

IMPORTANT DATA HANDLING:
- Focus on functional requirements and test scenarios only
- Do NOT generate, request, or repeat specific user identities (names, emails, usernames)
- Do NOT generate or request sensitive internal data (credentials, API keys, secrets)
- If input contains potentially sensitive data, reference it generically without repeating verbatim
- Prioritize test coverage and quality over metadata"""

    def _build_questioner_prompt(
        self,
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]]
    ) -> str:
        """Build the user prompt for question generation"""

        # Format child tickets with sanitization
        tickets_text = ""
        for ticket in child_tickets[:20]:  # Limit to avoid token overflow
            summary_safe = sanitize_prompt_input(ticket.get('summary', 'N/A'))
            tickets_text += f"\n- {ticket.get('key', 'N/A')}: {summary_safe}\n"
            if ticket.get('description'):
                # Truncate long descriptions and sanitize
                desc = ticket['description'][:300]
                desc_safe = sanitize_prompt_input(desc)
                tickets_text += f"  Description: {desc_safe}...\n"

        # Sanitize epic data to prevent prompt injection
        epic_summary_safe = sanitize_prompt_input(epic_data.get('summary', 'N/A'))
        epic_desc_safe = sanitize_prompt_input(epic_data.get('description', 'No description provided'))

        prompt = f"""Analyze the following Epic and generate specific questions to clarify gaps and ambiguities:

**Epic**: {epic_data.get('key', 'N/A')}
**Summary**: {epic_summary_safe}

**Description**:
{epic_desc_safe}

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

    def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Call LLM with structured output using Pydantic model

        Args:
            system_prompt: System prompt defining the agent's role
            user_prompt: User prompt with specific task details
            max_tokens: Maximum tokens for the response

        Returns:
            Tuple of (result dict, error message)
        """
        try:
            result, error = self.llm.complete_json(
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
                pydantic_model=QuestionerResponse
            )

            if error:
                return None, error

            # Parse the JSON string response into a dict
            if isinstance(result, str):
                import json
                parsed = json.loads(result)
                return parsed, None
            else:
                # Already a dict
                return result, None

        except Exception as e:
            return None, f"{self.name} structured LLM call failed: {str(e)}"
