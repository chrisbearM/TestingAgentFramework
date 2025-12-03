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
from pydantic import BaseModel, Field
from .base_agent import BaseAgent


# Pydantic models for structured output
class EpicCoverage(BaseModel):
    """Schema for epic requirements coverage"""
    covered_requirements: List[str] = Field(description="List of Epic requirements that are covered by test tickets")
    missing_requirements: List[str] = Field(description="List of Epic requirements not adequately covered")
    coverage_percentage: int = Field(description="Percentage of Epic requirements covered (0-100)", ge=0, le=100)


class ChildTicketCoverage(BaseModel):
    """Schema for child ticket coverage"""
    covered_tickets: List[str] = Field(description="List of child ticket keys fully covered by test tickets")
    partially_covered_tickets: List[str] = Field(description="List of child ticket keys partially covered", default_factory=list)
    uncovered_tickets: List[str] = Field(description="List of child ticket keys not covered at all")
    coverage_percentage: int = Field(description="Percentage of child tickets covered (0-100)", ge=0, le=100)


class CoverageGap(BaseModel):
    """Schema for a coverage gap"""
    type: str = Field(description="Type of gap: Epic Requirement, Child Ticket, or Scenario")
    description: str = Field(description="Description of what is missing")
    severity: str = Field(description="Severity level: Critical, Important, or Minor")
    recommendation: str = Field(description="How to address this gap")


class CoverageReviewResponse(BaseModel):
    """Complete response schema for coverage review"""
    coverage_score: int = Field(description="Overall coverage score (0-100)", ge=0, le=100)
    coverage_level: str = Field(description="Coverage level: Comprehensive, Adequate, or Insufficient")
    epic_coverage: EpicCoverage = Field(description="Epic requirements coverage analysis")
    child_ticket_coverage: ChildTicketCoverage = Field(description="Child ticket coverage analysis")
    gaps: List[CoverageGap] = Field(description="List of coverage gaps")
    strengths: List[str] = Field(description="List of what is well covered")
    recommendations: List[str] = Field(description="Specific actionable recommendations")
    overall_assessment: str = Field(description="Detailed narrative assessment of overall coverage")


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
        child_attachments: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        use_structured_output: bool = True
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

        if use_structured_output:
            result, error = self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=3000
            )

            if error:
                return None, error

            return result, None
        else:
            # Fallback to regular JSON mode
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
        return """QA Lead reviewing test coverage. Assess: Epic requirements, child tickets, test scenarios.

⚠️ CRITICAL - OUT OF SCOPE EXCLUSION:
- NEVER flag items marked as "Out of Scope", "out of scope", or "removed from scope" as coverage gaps
- If a requirement is explicitly listed under "Out of Scope" section, DO NOT include it in missing_requirements
- If text mentions "(one-way sync only)" or similar qualifiers, check if it's in the out-of-scope section
- Only assess coverage for IN-SCOPE requirements
- When in doubt, if something is mentioned in an "Out of Scope" section, skip it entirely

NOTE: Test tickets = existing + new. Child tickets = functional only (test tickets excluded).

COVERAGE:
- Epic: Objectives, AC, features, business value (IN-SCOPE ONLY)
- Child tickets: Each covered ≥1 test, complex = multiple, dependencies
- Gaps: Critical (core missing) | Important (edge, integration) | Minor (optional)

LEVELS:
90-100 Comprehensive | 70-89 Adequate | <70 Insufficient

JSON:
{
  "coverage_score": 85,
  "coverage_level": "...",
  "epic_coverage": {"covered_requirements": ["..."], "missing_requirements": ["..."], "coverage_percentage": 80},
  "child_ticket_coverage": {"covered_tickets": ["..."], "partially_covered_tickets": ["..."], "uncovered_tickets": ["..."], "coverage_percentage": 75},
  "gaps": [{"type": "...", "description": "...", "severity": "Critical|Important|Minor", "recommendation": "..."}],
  "strengths": ["..."],
  "recommendations": ["..."],
  "overall_assessment": "..."
}

IMPORTANT DATA HANDLING:
- Focus on functional requirements and test scenarios only
- Do NOT generate, request, or repeat specific user identities (names, emails, usernames)
- Do NOT generate or request sensitive internal data (credentials, API keys, secrets)
- If input contains potentially sensitive data, reference it generically without repeating verbatim
- Prioritize test coverage and quality over metadata

""" + BaseAgent.get_accuracy_principles()

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
        # IMPORTANT: Include full description to ensure "Out of Scope" section is visible
        # Truncate to 3000 chars to allow room for out-of-scope section
        full_desc = epic_data.get('description', 'No description provided')
        epic_desc = full_desc if len(full_desc) <= 3000 else full_desc[:3000] + "..."

        epic_text = f"""**Epic**: {epic_data.get('key', 'N/A')}
**Summary**: {epic_data.get('summary', 'N/A')}

**Description**:
{epic_desc}
"""

        # Format attachments
        print(f"DEBUG CoverageReviewer: Received {len(epic_attachments or [])} epic attachments and {len(child_attachments or {})} child attachment groups")
        attachment_context = self._format_attachments(epic_attachments or [], child_attachments or {})
        print(f"DEBUG CoverageReviewer: Formatted attachment context: {len(attachment_context)} characters")

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
                    # Include full document content for comprehensive coverage review
                    # (truncate only if extremely large to avoid token overflow)
                    max_chars = 10000  # Allow up to ~10k characters per document
                    doc_content = content[:max_chars] + "..." if len(content) > max_chars else content
                    output.append(f"  • {filename} - Document")
                    if doc_content:
                        output.append(f"    Full content:\n    {doc_content}")

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

    def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 3000
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
                pydantic_model=CoverageReviewResponse
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
