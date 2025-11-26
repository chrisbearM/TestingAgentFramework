"""
Requirements Fixer Agent - Generates fixes for test ticket coverage gaps

This agent takes coverage review results and generates:
- Updated test tickets to improve coverage
- New test tickets to address missing requirements
- Specific modifications to address identified gaps
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from pydantic import BaseModel, Field
from .base_agent import BaseAgent


# Pydantic models for structured output
class ChildTicketReference(BaseModel):
    """Reference to a child ticket"""
    key: str = Field(description="Ticket key (e.g., KEY-123)")
    summary: str = Field(description="Ticket summary")


class NewTestTicket(BaseModel):
    """Schema for a new test ticket"""
    summary: str = Field(description="New test ticket summary")
    description: str = Field(description="Detailed description with **Background**, **Test Scope**, and **Source Requirements** sections")
    acceptance_criteria: List[str] = Field(description="List of 5-8 black-box acceptance criteria starting with 'Verify...' or 'Confirm...'")
    addresses_gap: str = Field(description="Description of what gap this ticket addresses")
    covers_requirements: List[str] = Field(description="List of requirements or features this ticket covers")
    child_tickets: List[ChildTicketReference] = Field(description="List of child tickets this test ticket covers")


class TicketUpdate(BaseModel):
    """Schema for updating an existing test ticket"""
    original_ticket_id: str = Field(description="Identifier of the original ticket (key or index)")
    updated_summary: str = Field(description="Updated summary for the ticket")
    updated_description: str = Field(description="Updated description for the ticket")
    updated_acceptance_criteria: List[str] = Field(description="Updated acceptance criteria")
    changes_made: str = Field(description="Description of what was changed and why")
    addresses_gap: str = Field(description="Description of what gap this update addresses")


class FixesSummary(BaseModel):
    """Schema for fixes summary"""
    gaps_addressed: int = Field(description="Number of gaps addressed by the fixes", ge=0)
    new_tickets_count: int = Field(description="Number of new test tickets created", ge=0)
    updated_tickets_count: int = Field(description="Number of existing tickets updated", ge=0)
    estimated_coverage_improvement: int = Field(description="Estimated percentage improvement in coverage (0-100)", ge=0, le=100)


class RequirementsFixesResponse(BaseModel):
    """Complete response schema for requirements fixes"""
    new_tickets: List[NewTestTicket] = Field(description="List of new test tickets to create", default_factory=list)
    ticket_updates: List[TicketUpdate] = Field(description="List of updates to existing tickets", default_factory=list)
    summary: FixesSummary = Field(description="Summary of fixes and coverage improvement")


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
        child_tickets: List[Dict[str, Any]],
        epic_attachments: Optional[List[Dict[str, Any]]] = None,
        child_attachments: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        use_structured_output: bool = True
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Generate fixes for coverage gaps

        Args:
            coverage_review: Coverage review results from CoverageReviewerAgent
            existing_tickets: Current test tickets
            epic_data: Epic information
            child_tickets: Child tickets from the Epic
            epic_attachments: Optional list of epic attachments (documents, images)
            child_attachments: Optional dict mapping child keys to their attachments

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
                        "child_tickets": [{"key": "TICKET-1", "summary": "Ticket summary"}]
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
            child_tickets,
            epic_attachments,
            child_attachments
        )

        if use_structured_output:
            result, error = self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=3500
            )

            if error:
                return None, error

            return result, None
        else:
            # Fallback to regular JSON mode
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
        return """Test strategist fixing coverage gaps.

⚠️ CRITICAL - OUT OF SCOPE EXCLUSION:
- NEVER create test tickets for items marked as "Out of Scope", "out of scope", or "removed from scope"
- If a requirement is explicitly listed under "Out of Scope" section, DO NOT create ANY test tickets for it
- If text mentions "(one-way sync only)" or similar qualifiers, check if it's in the out-of-scope section
- Only create test tickets for IN-SCOPE requirements
- When in doubt, if something is mentioned in an "Out of Scope" section, skip it entirely

ACTIONS:
1. New tickets for uncovered IN-SCOPE requirements/child tickets only
2. Update existing tickets for gaps in IN-SCOPE functionality

NEW TICKETS:
- **Background**, **Test Scope**, **Source Requirements**
- 5-8 black-box AC ("Verify...", "Confirm...")
- Specify gap addressed

UPDATES:
- ID ticket, updated fields, changes, gap addressed

Priority: Critical > Important > Minor

JSON:
{
  "new_tickets": [{
    "summary": "...",
    "description": "**Background**\\n\\n...\\n\\n**Test Scope**\\n\\n...\\n\\n**Source Requirements**\\n\\n- KEY-X: ...",
    "acceptance_criteria": ["Verify...", "Confirm..."],
    "addresses_gap": "...",
    "covers_requirements": ["..."],
    "child_tickets": [{"key": "...", "summary": "..."}]
  }],
  "ticket_updates": [{
    "original_ticket_id": "...",
    "updated_summary": "...",
    "updated_description": "...",
    "updated_acceptance_criteria": ["..."],
    "changes_made": "...",
    "addresses_gap": "..."
  }],
  "summary": {"gaps_addressed": 5, "new_tickets_count": 1, "updated_tickets_count": 1, "estimated_coverage_improvement": 25}
}

IMPORTANT DATA HANDLING:
- Focus on functional requirements and test scenarios only
- Do NOT generate, request, or repeat specific user identities (names, emails, usernames)
- Do NOT generate or request sensitive internal data (credentials, API keys, secrets)
- If input contains potentially sensitive data, reference it generically without repeating verbatim
- Prioritize test coverage and quality over metadata

""" + BaseAgent.get_accuracy_principles()

    def _build_fixer_prompt(
        self,
        coverage_review: Dict[str, Any],
        existing_tickets: List[Dict[str, Any]],
        epic_data: Dict[str, Any],
        child_tickets: List[Dict[str, Any]],
        epic_attachments: Optional[List[Dict[str, Any]]] = None,
        child_attachments: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> str:
        """Build the user prompt for generating fixes"""

        # Format attachments
        attachment_context = self._format_attachments(epic_attachments or [], child_attachments or {})

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

{attachment_context}

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
        output.append("The following documents and mockups provide additional context for generating fixes:\n")

        # Epic attachments
        if epic_attachments:
            output.append("Epic Attachments:")
            for att in epic_attachments:
                filename = att.get('filename', 'Unknown')
                att_type = att.get('type', 'unknown')

                if att_type == 'image':
                    output.append(f"  • {filename} - UI Mockup/Screenshot")
                    output.append(f"    → Ensure test tickets cover UI elements shown in this mockup")
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

        output.append("\n**IMPORTANT**: When generating fixes, ensure new test tickets address requirements shown in these documents and mockups.\n")

        return "\n".join(output)

    def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 3500
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
                pydantic_model=RequirementsFixesResponse
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
