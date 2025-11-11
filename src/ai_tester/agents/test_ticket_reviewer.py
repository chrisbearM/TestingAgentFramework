"""
Test Ticket Reviewer Agent
Reviews generated test tickets and provides quality scores and feedback
"""

from typing import Dict, Any, Tuple, Optional
from .base_agent import BaseAgent


class TestTicketReviewerAgent(BaseAgent):
    """
    Reviews test tickets using BA/PM persona to ensure quality and completeness
    """

    def run(self, context: Dict[str, Any], **kwargs) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Review a generated test ticket

        Args:
            context: Dictionary containing:
                - ticket_data: Generated ticket with summary, description, acceptance_criteria
                - epic_context: Epic context for reference

        Returns:
            Tuple of (review_data, error_message)
        """
        ticket_data = context.get('ticket_data', {})
        epic_context = context.get('epic_context', {})

        return self.review_ticket(ticket_data, epic_context)

    def review_ticket(
        self,
        ticket_data: Dict[str, Any],
        epic_context: Dict[str, Any]
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Review test ticket and provide quality score with feedback

        Returns:
            Tuple of (review_dict, error_message)
        """

        system_prompt = """You are a Senior Product Manager / QA Lead reviewing test tickets.

EVALUATION CRITERIA:
1. Completeness (30 points):
   - Covers all in-scope functionality
   - No critical gaps
   - Source tickets properly listed

2. Clarity (25 points):
   - Clear, unambiguous acceptance criteria
   - Each AC is testable
   - No technical jargon

3. Structure (20 points):
   - Follows required format
   - Well-organized description
   - Proper AC formatting

4. Scope Accuracy (25 points):
   - Excludes out-of-scope items
   - Focuses on in-scope functionality
   - Appropriate granularity

OUTPUT: Return ONLY valid JSON:
{
  "quality_score": 85,
  "needs_improvement": false,
  "issues": ["Issue 1 if any", "Issue 2 if any"],
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "strengths": ["Strength 1", "Strength 2"]
}

Score 80+ = Excellent, 60-79 = Good, 40-59 = Needs improvement, <40 = Poor"""

        summary = ticket_data.get('summary', '')
        description = ticket_data.get('description', '')
        acceptance_criteria = ticket_data.get('acceptance_criteria', [])

        user_prompt = f"""Review this test ticket:

SUMMARY: {summary}

DESCRIPTION:
{description}

ACCEPTANCE CRITERIA ({len(acceptance_criteria)} items):
"""
        for i, ac in enumerate(acceptance_criteria, 1):
            user_prompt += f"{i}. {ac}\n"

        user_prompt += "\n\nProvide quality score and detailed feedback."

        result, error = self._call_llm(system_prompt, user_prompt, max_tokens=1500)

        if error:
            return None, error

        try:
            review_data = self._parse_json_response(result)
            return review_data, None
        except Exception as e:
            return None, f"Failed to parse review data: {str(e)}"
