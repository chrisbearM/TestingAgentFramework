"""
Requirements Fixer Agent - Generates fixes for test ticket coverage gaps

This agent takes coverage review results and generates:
- Updated test tickets to improve coverage
- New test tickets to address missing requirements
- Specific modifications to address identified gaps
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from .base_agent import BaseAgent


class RequirementsFixerAgent(BaseAgent):
    """
    Generates fixes for test ticket coverage gaps
    """

    def __init__(self, llm):
        super().__init__(llm)

    def generate_fixes(
        self,
        coverage_review: Dict[str, Any],
        existing_tickets: List[Dict[str, Any]],
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Generate fixes for coverage gaps

        Args:
            coverage_review: Coverage review results from CoverageReviewerAgent
            existing_tickets: Current test tickets
            epic_data: Epic information
            child_tickets: Child tickets from the Epic

        Returns:
            Tuple of (fixes result, error message)
            Result format:
            {
                "new_tickets": [
                    {
                        "summary": "New test ticket summary",
                        "description": "Detailed description",
                        "acceptance_criteria": ["AC 1", "AC 2"],
                        "addresses_gap": "What gap this fills",
                        "covers_requirements": ["Req 1", "Req 2"],
                        "covers_child_tickets": ["TICKET-1"]
                    }
                ],
                "ticket_updates": [
                    {
                        "original_ticket_id": "Ticket identifier or index",
                        "updated_summary": "Improved summary",
                        "updated_description": "Improved description",
                        "updated_acceptance_criteria": ["AC 1", "AC 2"],
                        "changes_made": "What was changed and why",
                        "addresses_gap": "What gap this addresses"
                    }
                ],
                "summary": {
                    "gaps_addressed": 5,
                    "new_tickets_count": 2,
                    "updated_tickets_count": 3,
                    "estimated_coverage_improvement": 25
                }
            }
        """
        system_prompt = self._get_fixer_system_prompt()
        user_prompt = self._build_fixer_prompt(
            coverage_review,
            existing_tickets,
            epic_data,
            child_tickets
        )

        result, error = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3500
        )

        if error:
            return None, error

        # Parse JSON response
        fixes_data = self._parse_json_response(result)
        if not fixes_data:
            return None, "Failed to parse fixes from response"

        return fixes_data, None

    def _get_fixer_system_prompt(self) -> str:
        """System prompt for Requirements Fixer Agent"""
        return """You are an expert Test Strategist and Requirements Engineer.

Your role is to analyze coverage gaps and generate specific fixes to improve test ticket coverage.

CRITICAL: IGNORE OUT-OF-SCOPE FUNCTIONALITY:
- If you see ANY mention of 'removed from scope', 'out of scope', or 'not in scope', DO NOT include that functionality
- DO NOT create test tickets for functionality that has been marked as removed or out of scope
- DO NOT update tickets to add coverage for out-of-scope features
- Only address gaps for functionality that is IN SCOPE
- When in doubt, exclude rather than include

When generating fixes, you can:
1. **Create New Test Tickets**: For missing requirements or uncovered child tickets
2. **Update Existing Tickets**: Enhance existing tickets to cover more requirements

For each fix:

**New Test Tickets**:
- Focus on addressing specific gaps (Epic requirements, child tickets, scenarios)
- Provide clear, detailed summary and description
- Include comprehensive acceptance criteria
- Specify what requirements/child tickets it covers
- Explain what gap it addresses

**Ticket Updates**:
- Identify which existing ticket to modify
- Provide updated summary, description, and acceptance criteria
- Explain what changes were made and why
- Show how the update addresses a specific gap

**Prioritization**:
- Address Critical gaps first (missing core functionality)
- Then Important gaps (edge cases, integration)
- Finally Minor gaps (optional features)

**Quality Guidelines**:
- Be specific and actionable
- Ensure each fix addresses at least one identified gap
- Avoid creating redundant test scenarios
- Maintain consistency with existing test tickets
- Use clear, testable acceptance criteria

Return ONLY valid JSON in this exact format:
{
  "new_tickets": [
    {
      "summary": "Test Export Functionality",
      "description": "Verify that users can export data in CSV and Excel formats with proper formatting and data integrity",
      "acceptance_criteria": [
        "Export button is visible and enabled when data is present",
        "CSV export contains all visible columns with correct data",
        "Excel export maintains formatting and formulas",
        "File downloads successfully with correct filename"
      ],
      "addresses_gap": "Critical gap: Export functionality is not tested",
      "covers_requirements": ["Export to CSV", "Export to Excel"],
      "covers_child_tickets": ["TICKET-4"]
    }
  ],
  "ticket_updates": [
    {
      "original_ticket_id": "Test Ticket 1",
      "updated_summary": "Test Dashboard Viewing and Filtering (Enhanced)",
      "updated_description": "Enhanced description that includes edge cases for large datasets and performance requirements",
      "updated_acceptance_criteria": [
        "Dashboard loads within 2 seconds",
        "Filters work correctly with all data types",
        "Edge case: Dashboard handles 10,000+ records gracefully"
      ],
      "changes_made": "Added performance requirement and edge case for large datasets",
      "addresses_gap": "Important gap: Performance and scalability not addressed"
    }
  ],
  "summary": {
    "gaps_addressed": 5,
    "new_tickets_count": 1,
    "updated_tickets_count": 1,
    "estimated_coverage_improvement": 25
  }
}"""

    def _build_fixer_prompt(
        self,
        coverage_review: Dict[str, Any],
        existing_tickets: List[Dict[str, Any]],
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]]
    ) -> str:
        """Build the user prompt for generating fixes"""

        # Format coverage review gaps
        gaps = coverage_review.get('gaps', [])
        gaps_text = "\n**Coverage Gaps to Address**:\n"
        for i, gap in enumerate(gaps, 1):
            gaps_text += f"\n{i}. [{gap.get('severity', 'Unknown')}] {gap.get('type', 'Gap')}\n"
            gaps_text += f"   Description: {gap.get('description', 'N/A')}\n"
            gaps_text += f"   Recommendation: {gap.get('recommendation', 'N/A')}\n"

        # Format missing requirements
        epic_coverage = coverage_review.get('epic_coverage', {})
        missing_reqs = epic_coverage.get('missing_requirements', [])
        missing_reqs_text = ""
        if missing_reqs and len(missing_reqs) > 0:
            missing_reqs_text = f"\n**Missing Epic Requirements** ({len(missing_reqs)}):\n"
            for req in missing_reqs[:10]:
                missing_reqs_text += f"- {req}\n"

        # Format uncovered child tickets
        child_coverage = coverage_review.get('child_ticket_coverage', {})
        uncovered = child_coverage.get('uncovered_tickets', [])
        partially_covered = child_coverage.get('partially_covered_tickets', [])
        uncovered_text = ""
        if uncovered or partially_covered:
            uncovered_text = "\n**Uncovered/Partially Covered Child Tickets**:\n"
            for ticket_key in uncovered[:5]:
                # Find the child ticket details
                ticket_info = next((t for t in child_tickets if t.get('key') == ticket_key), None)
                if ticket_info:
                    uncovered_text += f"- {ticket_key}: {ticket_info.get('summary', 'N/A')} [UNCOVERED]\n"
                else:
                    uncovered_text += f"- {ticket_key} [UNCOVERED]\n"
            for ticket_key in partially_covered[:5]:
                ticket_info = next((t for t in child_tickets if t.get('key') == ticket_key), None)
                if ticket_info:
                    uncovered_text += f"- {ticket_key}: {ticket_info.get('summary', 'N/A')} [PARTIAL]\n"
                else:
                    uncovered_text += f"- {ticket_key} [PARTIAL]\n"

        # Format existing tickets
        existing_text = f"\n**Existing Test Tickets** ({len(existing_tickets)}):\n"
        for i, ticket in enumerate(existing_tickets, 1):
            existing_text += f"\n{i}. {ticket.get('summary', 'N/A')}\n"
            desc = ticket.get('description', '')[:200]
            existing_text += f"   Description: {desc}...\n"

        # Recommendations
        recommendations = coverage_review.get('recommendations', [])
        rec_text = ""
        if recommendations and len(recommendations) > 0:
            rec_text = "\n**Coverage Reviewer Recommendations**:\n"
            for i, rec in enumerate(recommendations, 1):
                rec_text += f"{i}. {rec}\n"

        prompt = f"""Generate fixes to address coverage gaps in the test tickets:

**Epic**: {epic_data.get('key', 'N/A')} - {epic_data.get('summary', 'N/A')}

**Current Coverage Score**: {coverage_review.get('coverage_score', 0)}%
**Coverage Level**: {coverage_review.get('coverage_level', 'Unknown')}

{gaps_text}

{missing_reqs_text}

{uncovered_text}

{existing_text}

{rec_text}

Generate fixes to improve coverage:
1. Create NEW test tickets for missing requirements and uncovered child tickets
2. Suggest UPDATES to existing tickets to enhance coverage
3. Prioritize addressing Critical and Important gaps

For each fix:
- Be specific and actionable
- Reference the gap being addressed
- Provide complete ticket details (summary, description, acceptance criteria)
- Identify which requirements or child tickets are covered

Return ONLY the JSON response with your fixes."""

        return prompt
