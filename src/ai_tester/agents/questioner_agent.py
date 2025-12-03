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

        # Format attachments if available
        attachments_section = self._format_attachments(epic_data)

        prompt = f"""Analyze the following Epic and generate specific questions to clarify gaps and ambiguities:

**Epic**: {epic_data.get('key', 'N/A')}
**Summary**: {epic_summary_safe}

**Description**:
{epic_desc_safe}

{attachments_section}

**Child Tickets** ({len(child_tickets)} total):
{tickets_text}

Generate 5-10 targeted questions that would help clarify requirements and ensure comprehensive test coverage.

IMPORTANT: If uploaded documents or attachments provide specific answers to potential questions (e.g., field specifications, data formats, validation rules, UI mockups), DO NOT ask questions about those areas. Focus on gaps that are NOT covered by the provided documents.

Focus on:
- What is unclear or ambiguous (that is NOT answered by attached documents)?
- What edge cases are not addressed?
- What integration points are undefined?
- What acceptance criteria are missing?
- What error scenarios are not specified?

Return ONLY the JSON response with your questions."""

        return prompt

    def _format_attachments(self, epic_data: Dict[str, Any]) -> str:
        """
        Format attachments for inclusion in prompt.

        Args:
            epic_data: Epic data containing attachments

        Returns:
            Formatted string representation of attachments
        """
        epic_attachments = epic_data.get('epic_attachments', [])
        child_attachments = epic_data.get('child_attachments', {})

        if not epic_attachments and not child_attachments:
            return ""

        output = ["\n**UPLOADED DOCUMENTS & ATTACHMENTS**:"]

        # Epic attachments
        if epic_attachments:
            output.append("\nEpic Attachments:")
            for att in epic_attachments:
                filename = att.get('filename', 'Unknown')
                att_type = att.get('type', 'unknown')

                if att_type == 'document':
                    content = att.get('content', '')
                    # Include full document content for comprehensive analysis
                    # (truncate only if extremely large to avoid token overflow)
                    max_chars = 10000  # Allow up to ~10k characters per document
                    doc_content = content[:max_chars] + "..." if len(content) > max_chars else content
                    output.append(f"  • {filename} (Document)")
                    if doc_content:
                        output.append(f"    Full content:\n{doc_content}")
                elif att_type == 'image':
                    output.append(f"  • {filename} (Image/UI Mockup)")

        # Child ticket attachments (images only for brevity)
        image_count = 0
        if child_attachments:
            for child_key, attachments in child_attachments.items():
                for att in attachments:
                    if att.get('type') == 'image':
                        image_count += 1

        if image_count > 0:
            output.append(f"\nChild Ticket Attachments: {image_count} UI mockups/screenshots")

        output.append("\n→ These documents/attachments provide additional context. Do NOT ask questions about information that is clearly specified in these documents.")

        return "\n".join(output)

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
