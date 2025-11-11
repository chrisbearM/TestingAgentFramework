"""
Test Ticket Generator Agent
Generates comprehensive test tickets based on Epic context and strategic options
"""

from typing import Dict, List, Any, Tuple, Optional
import json
from .base_agent import BaseAgent
from ai_tester.utils.jira_text_cleaner import clean_jira_text_for_llm


class TestTicketGeneratorAgent(BaseAgent):
    """
    Generates comprehensive test tickets based on Epic analysis and strategic planning.
    Follows BA/PO persona with focus on black-box acceptance criteria.
    """

    def run(self, context: Dict[str, Any], **kwargs) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Generate a single test ticket

        Args:
            context: Dictionary containing:
                - epic_name: Epic name/summary
                - functional_area: Functional area this ticket covers
                - child_tickets: List of child ticket dictionaries
                - epic_context: Full epic context (description, etc.)
                - previous_attempt: Optional previous attempt (for refinement)
                - reviewer_feedback: Optional review feedback (for refinement)

        Returns:
            Tuple of (ticket_data, error_message)
        """
        epic_name = context.get('epic_name', '')
        functional_area = context.get('functional_area', '')
        child_tickets = context.get('child_tickets', [])
        epic_context = context.get('epic_context', {})
        previous_attempt = context.get('previous_attempt')
        reviewer_feedback = context.get('reviewer_feedback')

        return self.generate_test_ticket(
            epic_name,
            functional_area,
            child_tickets,
            epic_context,
            previous_attempt,
            reviewer_feedback
        )

    def generate_test_ticket(
        self,
        epic_name: str,
        functional_area: str,
        child_tickets: List[Dict],
        epic_context: Dict,
        previous_attempt: Optional[str] = None,
        reviewer_feedback: Optional[Dict] = None
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Generate a single test ticket using BA/PO persona

        Returns:
            Tuple of (ticket_data_dict, error_message)
        """

        if previous_attempt and reviewer_feedback:
            system_prompt = self._get_refinement_system_prompt()
            user_prompt = self._build_refinement_prompt(
                previous_attempt,
                reviewer_feedback,
                epic_name,
                functional_area
            )
        else:
            system_prompt = self._get_generation_system_prompt()
            user_prompt = self._build_generation_prompt(
                epic_name,
                functional_area,
                child_tickets,
                epic_context
            )

        result, error = self._call_llm(system_prompt, user_prompt, max_tokens=3000)

        if error:
            return None, error

        try:
            ticket_data = self._parse_json_response(result)
            return ticket_data, None
        except Exception as e:
            return None, f"Failed to parse ticket data: {str(e)}"

    def _get_generation_system_prompt(self) -> str:
        """System prompt for generating new test tickets"""
        return """You are a Senior Business Analyst / Product Owner tasked with creating test tickets for a QA team.

YOUR ROLE:
- Analyze the Epic and child tickets to understand the feature
- Create a comprehensive test ticket for this functional area
- Match the Epic author's writing style (tone, terminology, structure)
- Focus on BLACK-BOX acceptance criteria for manual testing

CRITICAL: IGNORE OUT-OF-SCOPE FUNCTIONALITY:
- If you see ANY mention of 'removed from scope', 'out of scope', or 'not in scope', DO NOT include that functionality
- If delete operations are marked as removed, DO NOT create test cases for delete
- Only test functionality that is IN SCOPE
- When in doubt, exclude rather than include

CRITICAL REQUIREMENTS:
1. Summary: Follow format '[Epic Name] - Testing - [Functional Area]'
2. Description:
   - Overview of what this test ticket covers
   - Clear scope definition
   - Written in Epic author's style
3. Acceptance Criteria:
   - 5-8 black-box acceptance criteria
   - Each AC must be testable by a manual QA tester
   - NO technical implementation details
4. Source Tickets:
   - Include at END of description: 'Source Tickets: KEY-123, KEY-124'

OUTPUT: Return ONLY valid JSON:
{
  "summary": "[Epic Name] - Testing - [Functional Area]",
  "description": "Overview...\n\nSource Tickets: KEY-1, KEY-2",
  "acceptance_criteria": ["AC 1", "AC 2", "AC 3"]
}"""

    def _get_refinement_system_prompt(self) -> str:
        return """You are a Senior Business Analyst improving a rejected test ticket.

Fix issues from feedback while maintaining:
- Epic author's writing style
- Source Tickets section at end
- Black-box acceptance criteria
- Exclusion of out-of-scope functionality

OUTPUT: Return ONLY valid JSON:
{
  "summary": "[Epic Name] - Testing - [Functional Area]",
  "description": "Improved description...",
  "acceptance_criteria": ["Improved AC 1", "Improved AC 2"]
}"""

    def _build_generation_prompt(self, epic_name: str, functional_area: str,
                                 child_tickets: List[Dict], epic_context: Dict) -> str:
        epic_desc = epic_context.get('epic_desc', '')
        epic_desc_cleaned = clean_jira_text_for_llm(epic_desc) if epic_desc else ''

        child_context = "\n\nChild Tickets:\n"
        for child in child_tickets[:20]:
            key = child.get('key', '')
            summary = child.get('summary', '')
            desc = child.get('desc', '')
            desc_cleaned = clean_jira_text_for_llm(desc) if desc else ''
            child_context += f"\n{key}: {summary}\n"
            if desc_cleaned:
                child_context += f"  {desc_cleaned[:300]}...\n"

        # Format attachments
        attachment_context = self._format_attachments(epic_context)

        return f"""Epic: {epic_context.get('epic_key', '')} - {epic_name}

Epic Description:
{epic_desc_cleaned[:1000]}

{attachment_context}

{child_context}

Create test ticket for '{functional_area}'.
Include Source Tickets section with all relevant child ticket keys.

IMPORTANT: If there are UI mockups or screenshots attached, ensure you create acceptance criteria that test the visual/interface aspects shown in those mockups."""

    def _build_refinement_prompt(self, previous_attempt: str, reviewer_feedback: Dict,
                                epic_name: str, functional_area: str) -> str:
        prompt = f"""PREVIOUS ATTEMPT (REJECTED):
{previous_attempt}

FEEDBACK (Score: {reviewer_feedback.get('quality_score', 0)}/100):
Issues:
"""
        for issue in reviewer_feedback.get('issues', []):
            prompt += f"- {issue}\n"
        prompt += "\nRecommendations:\n"
        for rec in reviewer_feedback.get('recommendations', []):
            prompt += f"- {rec}\n"
        prompt += f"\n\nCreate improved version for '{functional_area}'."""
        return prompt

    def _format_attachments(self, epic_context: Dict) -> str:
        """
        Format attachments for inclusion in prompt.

        Args:
            epic_context: Epic context containing attachments

        Returns:
            Formatted string representation of attachments
        """
        epic_attachments = epic_context.get('epic_attachments', [])
        child_attachments = epic_context.get('child_attachments', {})

        if not epic_attachments and not child_attachments:
            return ""

        output = ["\nATTACHMENTS:"]

        # Epic attachments
        if epic_attachments:
            for att in epic_attachments:
                filename = att.get('filename', 'Unknown')
                att_type = att.get('type', 'unknown')

                if att_type == 'image':
                    output.append(f"  • {filename} - UI Mockup/Screenshot showing visual requirements")
                elif att_type == 'document':
                    content = att.get('content', '')
                    preview = content[:200] + "..." if len(content) > 200 else content
                    output.append(f"  • {filename} - Document")
                    if preview:
                        output.append(f"    → {preview}")

        # Child ticket attachments (only show images for UI testing)
        ui_mockups_count = 0
        if child_attachments:
            for child_key, attachments in child_attachments.items():
                for att in attachments:
                    if att.get('type') == 'image':
                        ui_mockups_count += 1
                        filename = att.get('filename', 'Unknown')
                        output.append(f"  • {child_key}/{filename} - UI Mockup/Screenshot")

        if ui_mockups_count > 0:
            output.append(f"\n  → TOTAL: {ui_mockups_count + len([a for a in epic_attachments if a.get('type') == 'image'])} UI mockups/screenshots found")
            output.append("  → Create acceptance criteria to verify UI elements, layouts, and interactions shown in mockups")

        return "\n".join(output)
