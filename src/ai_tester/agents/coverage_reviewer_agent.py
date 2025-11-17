"""
Coverage Reviewer Agent - Reviews test ticket coverage against Epic and child tickets

This agent analyzes generated test tickets to ensure:
- All Epic requirements are comprehensively covered
- All child tickets are addressed by test tickets
- No critical gaps in test coverage
- Appropriate depth and breadth of testing
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from .base_agent import BaseAgent


class CoverageReviewerAgent(BaseAgent):
    """
    Reviews test ticket coverage for completeness and quality
    """

    def __init__(self, llm):
        super().__init__(llm)

    def review_coverage(
        self,
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]],
        test_tickets: List[Dict[str, Any]],
        epic_attachments: Optional[List[Dict[str, Any]]] = None,
        child_attachments: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Review test ticket coverage against Epic and child tickets

        Args:
            epic_data: Epic information (key, summary, description)
            child_tickets: List of functional child tickets from the Epic (excluding existing test tickets)
            test_tickets: All test tickets including both existing and newly generated ones
            epic_attachments: Optional list of epic attachments (documents, images)
            child_attachments: Optional dict mapping child keys to their attachments

        Returns:
            Tuple of (coverage review result, error message)
            Result format:
            {
                "coverage_score": 85,  # 0-100
                "coverage_level": "Comprehensive|Adequate|Insufficient",
                "epic_coverage": {
                    "covered_requirements": ["Req 1", "Req 2"],
                    "missing_requirements": ["Req 3"],
                    "coverage_percentage": 85
                },
                "child_ticket_coverage": {
                    "covered_tickets": ["TICKET-1", "TICKET-2"],
                    "partially_covered_tickets": ["TICKET-3"],
                    "uncovered_tickets": ["TICKET-4"],
                    "coverage_percentage": 75
                },
                "gaps": [
                    {
                        "type": "Epic Requirement|Child Ticket|Scenario",
                        "description": "What is missing",
                        "severity": "Critical|Important|Minor",
                        "recommendation": "How to address"
                    }
                ],
                "strengths": [
                    "What is well covered"
                ],
                "recommendations": [
                    "Specific actionable recommendations"
                ],
                "overall_assessment": "Detailed narrative assessment"
            }
        """
        system_prompt = self._get_reviewer_system_prompt()
        user_prompt = self._build_reviewer_prompt(
            epic_data,
            child_tickets,
            test_tickets,
            epic_attachments,
            child_attachments
        )

        result, error = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000
        )

        if error:
            return None, error

        # Parse JSON response
        review_data = self._parse_json_response(result)
        if not review_data or 'coverage_score' not in review_data:
            return None, "Failed to parse coverage review from response"

        return review_data, None

    def _get_reviewer_system_prompt(self) -> str:
        """System prompt for Coverage Reviewer Agent"""
        return """You are an expert Test Strategist and Quality Assurance Lead.

Your role is to review test tickets and assess whether they provide comprehensive coverage of:
1. **Epic Requirements**: All objectives, features, and acceptance criteria in the Epic
2. **Child Tickets**: All functional user stories, tasks, and sub-tasks under the Epic
3. **Test Scenarios**: Appropriate breadth and depth of testing

**IMPORTANT**: You will receive:
- Test tickets that include BOTH existing test tickets (already in Jira) AND newly generated test tickets
- Child tickets that are ONLY functional tickets (existing test tickets have been filtered out)
- When calculating coverage, count BOTH existing and newly generated test tickets

When reviewing coverage, analyze:

**Epic Coverage**:
- Are all Epic objectives addressed by test tickets (existing + new)?
- Do test tickets cover the Epic's acceptance criteria?
- Are key features and functionality tested?
- Is the Epic's business value validated through testing?

**Child Ticket Coverage**:
- Is each functional child ticket addressed by at least one test ticket (existing or new)?
- Are complex child tickets covered by multiple test scenarios?
- Do test tickets validate child ticket acceptance criteria?
- Are dependencies between child tickets tested?
- IMPORTANT: Give credit for existing test tickets when they cover functional requirements

**Gap Analysis**:
Identify gaps in:
- **Critical Gaps**: Missing core functionality, untested requirements, uncovered child tickets
- **Important Gaps**: Incomplete edge case coverage, missing integration scenarios
- **Minor Gaps**: Optional features, nice-to-have scenarios

**Coverage Levels**:
- **Comprehensive (90-100)**: All requirements covered with appropriate depth, edge cases addressed
- **Adequate (70-89)**: Core requirements covered, some minor gaps acceptable
- **Insufficient (<70)**: Critical gaps exist, major requirements missing

For each gap identified:
- Specify what is missing (Epic requirement, child ticket, or scenario)
- Assess severity (Critical, Important, Minor)
- Provide specific recommendation to address the gap

Return ONLY valid JSON in this exact format:
{
  "coverage_score": 85,
  "coverage_level": "Comprehensive",
  "epic_coverage": {
    "covered_requirements": ["User can view dashboard", "Filters work correctly"],
    "missing_requirements": ["Export functionality"],
    "coverage_percentage": 80
  },
  "child_ticket_coverage": {
    "covered_tickets": ["TICKET-1", "TICKET-2"],
    "partially_covered_tickets": ["TICKET-3"],
    "uncovered_tickets": ["TICKET-4"],
    "coverage_percentage": 75
  },
  "gaps": [
    {
      "type": "Epic Requirement",
      "description": "Export functionality is not tested",
      "severity": "Critical",
      "recommendation": "Add test ticket for export feature with CSV and Excel formats"
    }
  ],
  "strengths": [
    "Core dashboard functionality is well covered",
    "Edge cases for filters are thoroughly tested"
  ],
  "recommendations": [
    "Add test ticket for export functionality",
    "Consider adding performance testing for large datasets"
  ],
  "overall_assessment": "The test tickets provide adequate coverage of the Epic with good depth on core features. However, export functionality and some child tickets need additional test coverage."
}"""

    def _build_reviewer_prompt(
        self,
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]],
        test_tickets: List[Dict[str, Any]],
        epic_attachments: Optional[List[Dict[str, Any]]] = None,
        child_attachments: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> str:
        """Build the user prompt for coverage review"""

        # Format Epic info
        epic_text = f"""**Epic**: {epic_data.get('key', 'N/A')}
**Summary**: {epic_data.get('summary', 'N/A')}

**Description**:
{epic_data.get('description', 'No description provided')[:1000]}
"""

        # Format attachments
        attachment_context = self._format_attachments(epic_attachments or [], child_attachments or {})

        # Format child tickets (functional only, test tickets excluded)
        child_tickets_text = f"\n**Functional Child Tickets** ({len(child_tickets)} total - test tickets excluded):\n"
        child_tickets_text += "\nThese are the functional requirements that need test coverage:\n"
        for ticket in child_tickets[:20]:  # Limit to avoid token overflow
            child_tickets_text += f"\n- **{ticket.get('key', 'N/A')}**: {ticket.get('summary', 'N/A')}\n"
            desc = ticket.get('description', '')
            if desc:
                child_tickets_text += f"  Description: {desc[:200]}...\n"

        # Format test tickets (includes both existing and newly generated)
        test_tickets_text = f"\n**Test Tickets for Coverage Analysis** ({len(test_tickets)} total):\n"
        test_tickets_text += "\nNOTE: This includes both existing test tickets from Jira AND newly generated test tickets.\n"
        test_tickets_text += "When calculating coverage, count ALL of these test tickets.\n\n"

        for i, ticket in enumerate(test_tickets, 1):
            # Determine if it's an existing ticket (has a Jira key format) or new (has TT format)
            ticket_key = ticket.get('id', ticket.get('key', ''))
            is_existing = '-TT-' not in str(ticket_key)
            ticket_type = "[EXISTING]" if is_existing else "[NEW]"

            test_tickets_text += f"\n{i}. {ticket_type} **{ticket.get('summary', 'N/A')}**\n"
            test_tickets_text += f"   Description: {ticket.get('description', 'N/A')[:300]}\n"

            # Include acceptance criteria if available
            ac = ticket.get('acceptance_criteria', [])
            if ac and len(ac) > 0:
                test_tickets_text += f"   Acceptance Criteria: {len(ac)} items\n"

            # Include source tickets if available
            source = ticket.get('child_tickets', [])
            if source and len(source) > 0:
                source_keys = [t.get('key', '') for t in source if isinstance(t, dict)]
                test_tickets_text += f"   Covers: {', '.join(source_keys)}\n"

        prompt = f"""Review test ticket coverage for this Epic.

{epic_text}

{attachment_context}

{child_tickets_text}

{test_tickets_text}

Perform a comprehensive coverage review:

1. **Epic Coverage**: Do the test tickets (existing + new) cover all Epic requirements and objectives?
2. **Child Ticket Coverage**: Is each functional child ticket addressed by test tickets (existing or new)?
3. **Gap Analysis**: What functional requirements are still missing test coverage?
4. **Strengths**: What is well covered by existing and new test tickets?
5. **Recommendations**: Specific actions to improve coverage

IMPORTANT REMINDERS:
- Count BOTH existing and newly generated test tickets when calculating coverage
- Existing test tickets provide just as much coverage as newly generated ones
- Only functional child tickets need to be covered (test tickets were filtered out)
- Give full credit for comprehensive existing test coverage

Provide a coverage score (0-100) and detailed analysis.

Return ONLY the JSON response with your review."""

        return prompt

    def _format_attachments(
        self,
        epic_attachments: List[Dict[str, Any]],
        child_attachments: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """
        Format attachments for inclusion in prompt.

        Args:
            epic_attachments: List of epic attachment dictionaries
            child_attachments: Dict mapping child ticket keys to their attachments

        Returns:
            Formatted string representation of attachments
        """
        if not epic_attachments and not child_attachments:
            return ""

        output = ["\n**ATTACHMENTS & DOCUMENTATION**:"]
        output.append("The following documents and mockups provide additional context for coverage review:\n")

        # Epic attachments
        if epic_attachments:
            output.append("Epic Attachments:")
            for att in epic_attachments:
                filename = att.get('filename', 'Unknown')
                att_type = att.get('type', 'unknown')

                if att_type == 'image':
                    output.append(f"  • {filename} - UI Mockup/Screenshot")
                    output.append(f"    → Verify test tickets cover UI elements shown in this mockup")
                elif att_type == 'document':
                    content = att.get('content', '')
                    preview = content[:300] + "..." if len(content) > 300 else content
                    output.append(f"  • {filename} - Document")
                    if preview:
                        output.append(f"    Content: {preview}")

        # Child ticket attachments
        if child_attachments:
            output.append("\nChild Ticket Attachments:")
            for child_key, attachments in list(child_attachments.items())[:5]:  # Limit to first 5
                output.append(f"  {child_key}:")
                for att in attachments:
                    filename = att.get('filename', 'Unknown')
                    att_type = att.get('type', 'unknown')
                    if att_type == 'image':
                        output.append(f"    • {filename} - UI Mockup/Screenshot")
                    elif att_type == 'document':
                        output.append(f"    • {filename} - Document")

        output.append("\n**IMPORTANT**: When reviewing coverage, ensure test tickets address requirements shown in these documents and mockups.\n")

        return "\n".join(output)
