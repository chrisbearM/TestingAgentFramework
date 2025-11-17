"""
Ticket Improver Agent - Generates improved versions of Epic/child tickets

This agent analyzes tickets and creates enhanced versions with:
- Clearer acceptance criteria
- More detailed descriptions
- Edge cases and error scenarios
- Better structured requirements
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from .base_agent import BaseAgent


class TicketImproverAgent(BaseAgent):
    """
    Generates improved versions of Jira tickets
    """

    def __init__(self, llm):
        super().__init__(llm)

    def improve_ticket(
        self,
        ticket_data: Dict[str, Any],
        questions: Optional[List[Dict[str, Any]]] = None,
        epic_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Generate an improved version of a ticket

        Args:
            ticket_data: Original ticket (key, summary, description)
            questions: Optional questions from readiness assessment
            epic_context: Optional Epic context for additional information

        Returns:
            Tuple of (improvement result, error message)
            Result format:
            {
                "improved_ticket": {
                    "summary": "Enhanced summary",
                    "description": "Improved description",
                    "acceptance_criteria": ["Clear AC 1", "Clear AC 2"],
                    "edge_cases": ["Edge case 1"],
                    "error_scenarios": ["Error scenario 1"]
                },
                "improvements_made": [
                    {
                        "area": "Acceptance Criteria",
                        "change": "What was changed",
                        "rationale": "Why it was changed"
                    }
                ],
                "quality_increase": 75  # Estimated quality improvement percentage
            }
        """
        system_prompt = self._get_improver_system_prompt()
        user_prompt = self._build_improver_prompt(ticket_data, questions, epic_context)

        result, error = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000  # Increased to handle longer descriptions and more ACs
        )

        if error:
            return None, error

        # Parse JSON response
        improvement_data = self._parse_json_response(result)
        if not improvement_data or 'improved_ticket' not in improvement_data:
            return None, "Failed to parse improvement from response"

        return improvement_data, None

    def _get_improver_system_prompt(self) -> str:
        """System prompt for Ticket Improver Agent"""
        return """You are an expert Business Analyst and Requirements Engineer.

Your role is to analyze Jira tickets and create improved versions that are:
1. **Clear and Unambiguous**: Remove vague language, clarify intent
2. **Complete**: Include all necessary details for implementation and testing
3. **Testable**: Clear acceptance criteria that can be verified
4. **Comprehensive**: Address edge cases, error handling, and integration points
5. **Style-Consistent**: MATCH the writing style, tone, and terminology of the original ticket author

CRITICAL: IGNORE OUT-OF-SCOPE FUNCTIONALITY:
- If you see ANY mention of 'removed from scope', 'out of scope', or 'not in scope', DO NOT include that functionality
- DO NOT add, expand on, or improve out-of-scope features
- DO NOT create acceptance criteria or edge cases for removed functionality
- Only improve functionality that is IN SCOPE
- When in doubt, exclude rather than include

CRITICAL: WRITING STYLE PRESERVATION
- Analyze the original ticket's writing style (formal/informal, technical/business-focused, terse/verbose)
- Match the tone, voice, and terminology used by the original author
- Preserve the structural format (bullet points, paragraphs, sections) if it works well
- Use the same technical terminology and jargon as the original
- If the original uses specific phrasing patterns, maintain those patterns
- The improved ticket should feel like it was written by the same person, just with more clarity and detail

When improving tickets, focus on:

**Summary**:
- Make it concise but descriptive
- Use action verbs (Add, Update, Fix, Implement)
- Include the key benefit or outcome

**Description**:
- MUST be well-structured with clear sections using markdown headers (##)
- Use proper paragraph breaks and line spacing for readability
- Structure as:
  ## Background
  [Context and why this work is needed]

  ## User Story
  As a [user type], I want [functionality] so that [benefit]

  ## Requirements
  - Bullet points for each specific requirement
  - Clear and testable statements

  ## Technical Considerations (if applicable)
  - Integration points
  - Data requirements
  - Performance considerations
- Explain the "why" not just the "what"
- Include user personas or use cases if relevant
- Reference related tickets or dependencies
- NEVER return a wall of text - always use formatting

**Acceptance Criteria**:
- CRITICAL: Match the format used in the original ticket (Rule-oriented OR Given-When-Then)
- Rule-oriented format: Simple pass/fail statements (e.g., "The user must be logged in to view dashboard")
- Given-When-Then format: Only use if original ticket uses this format
- Extract ALL testable requirements from the description text, not just explicit AC
- Cover positive and negative scenarios
- Include specific values/thresholds mentioned in description
- Address data validation requirements
- Include UI specifications (button labels, field requirements, validation rules) as separate AC items

**Edge Cases**:
- Boundary conditions
- Null/empty/invalid inputs
- Concurrent operations
- Large data volumes
- Network failures or timeouts

**Error Scenarios**:
- What should happen when things go wrong
- Error messages shown to users
- Logging and monitoring requirements
- Graceful degradation

For each improvement, explain:
- What was changed
- Why it needed improvement
- How it enhances clarity/testability
- Note if writing style was preserved

Return ONLY valid JSON in this exact format:
{
  "improved_ticket": {
    "summary": "Enhanced summary (in original author's style)",
    "description": "## Background\\n\\nContext explaining why this work is needed and what problem it solves.\\n\\n## User Story\\n\\nAs a [user type], I want [functionality] so that [benefit].\\n\\n## Requirements\\n\\n- Specific requirement 1\\n- Specific requirement 2\\n- Specific requirement 3\\n\\n## Technical Considerations\\n\\n- Integration point 1\\n- Data requirement 1",
    "acceptance_criteria": [
      "The form displays a heading of 'Enquiry'",
      "The close button displays 'x' with hover text 'Close'",
      "The First name field is required and accepts free text",
      "The Last name field is required and accepts free text",
      "The Email field validates for proper email format",
      "The Send button is disabled until all required fields are completed",
      "Form data is retained during the session when Cancel is clicked",
      "Form data is lost when browser is refreshed or closed"
    ],
    "edge_cases": ["Edge case 1", "Edge case 2"],
    "error_scenarios": ["Error scenario 1", "Error scenario 2"],
    "technical_notes": "Optional technical implementation notes"
  },
  "improvements_made": [
    {
      "area": "Writing Style",
      "change": "Preserved author's formal tone and technical terminology",
      "rationale": "Maintains consistency with original author's voice"
    },
    {
      "area": "Description Structure",
      "change": "Organized into clear sections with markdown headers",
      "rationale": "Improves readability and ensures all key information is captured"
    },
    {
      "area": "Acceptance Criteria",
      "change": "Extracted implicit requirements from description into explicit AC items",
      "rationale": "Description contained testable requirements that were not captured as AC"
    }
  ],
  "quality_increase": 75
}

IMPORTANT:
- The description field MUST contain newline characters (\\n) to create proper formatting. Do NOT return a single paragraph.
- Extract ALL testable requirements from the description text and add them as acceptance criteria.
- Use Rule-oriented format (simple statements) unless the original ticket uses Given-When-Then.
- Each UI element, validation rule, and behavior mentioned in description should become a separate AC item."""

    def _build_improver_prompt(
        self,
        ticket_data: Dict[str, Any],
        questions: Optional[List[Dict[str, Any]]],
        epic_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the user prompt for ticket improvement"""

        # Build questions context if provided
        questions_text = ""
        if questions and len(questions) > 0:
            questions_text = "\n\n**Questions to Address**:\n"
            for i, q in enumerate(questions[:5], 1):  # Limit to top 5
                questions_text += f"{i}. {q.get('question', 'N/A')}\n"

        # Build epic context if provided
        epic_text = ""
        if epic_context:
            epic_text = f"\n\n**Epic Context**:\n"
            epic_text += f"Epic: {epic_context.get('key', 'N/A')}\n"
            epic_text += f"Summary: {epic_context.get('summary', 'N/A')}\n"

        prompt = f"""Analyze and improve the following Jira ticket:

**Original Ticket**: {ticket_data.get('key', 'N/A')}
**Summary**: {ticket_data.get('summary', 'N/A')}

**Description**:
{ticket_data.get('description', 'No description provided')}

{epic_text}
{questions_text}

Generate an improved version of this ticket that:
1. MATCHES the writing style, tone, and terminology of the original author
2. Has a clearer, more descriptive summary (but in the same style)
3. Provides comprehensive description with context
4. Includes specific, testable acceptance criteria
5. Addresses edge cases and error scenarios
6. Incorporates answers to any questions raised (if provided)

CRITICAL: Study the original ticket's writing style carefully:
- Formal or informal tone?
- Technical depth and terminology used
- Sentence structure and phrasing patterns
- Use of bullet points, sections, or paragraphs
- Level of detail and verbosity

Your improved ticket should read as if the same person wrote it, just with more clarity, completeness, and structure.

Return ONLY the JSON response with the improved ticket."""

        return prompt
