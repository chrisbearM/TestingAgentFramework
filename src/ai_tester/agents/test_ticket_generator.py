"""
Test Ticket Generator Agent
Generates comprehensive test tickets based on Epic context and strategic options
"""

from typing import Dict, List, Any, Tuple, Optional
import json
from pydantic import BaseModel, Field
from .base_agent import BaseAgent
from ai_tester.utils.jira_text_cleaner import clean_jira_text_for_llm, sanitize_prompt_input


# Pydantic models for structured output
class ChildTicketReference(BaseModel):
    """Reference to a child ticket"""
    key: str = Field(description="Ticket key (e.g., KEY-123)")
    summary: str = Field(description="Ticket summary")


class TestTicketResponse(BaseModel):
    """Schema for test ticket generation response"""
    summary: str = Field(description="Test ticket summary in format: '[Epic] - Testing - [Area]'")
    description: str = Field(description="Test ticket description with **Background**, **Test Scope**, and **Source Requirements** sections")
    acceptance_criteria: List[str] = Field(description="List of rule-oriented acceptance criteria starting with 'Verify...' or 'Confirm...'. Create one AC per distinct requirement/field/constraint - could be 1 AC or 15+ ACs depending on scope.")
    child_tickets: List[ChildTicketReference] = Field(description="List of source child tickets that this test ticket covers")


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
        reviewer_feedback: Optional[Dict] = None,
        use_structured_output: bool = True
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Generate a single test ticket using BA/PO persona

        Args:
            epic_name: Epic name/summary
            functional_area: Functional area this ticket covers
            child_tickets: List of child ticket dictionaries
            epic_context: Full epic context (description, attachments, etc.)
            previous_attempt: Optional previous attempt (for refinement)
            reviewer_feedback: Optional review feedback (for refinement)
            use_structured_output: Whether to use OpenAI structured outputs (default: True)

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

        if use_structured_output:
            # Use structured output with Pydantic model
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
        return """Senior BA/PO creating QA test tickets. Match Epic author's style. Focus on black-box manual testing.

SCOPE RULES:
- Exclude 'out of scope' or 'removed from scope' features
- When uncertain, exclude

ACCEPTANCE CRITERIA SPECIFICITY:
- Extract SPECIFIC details from requirements (field names, formats, validation rules, data types, expected values)
- If specifications mention specific fields (e.g., "clientNumber", "unitNumber", "VIN"), reference those exact field names in ACs
- If formats are specified (e.g., "7 digits with leading zeros", "MM/DD/YYYY", "17 characters"), include those exact constraints
- If value constraints exist (e.g., "must be positive", "static value '17647'", "no decimals"), include those in ACs
- AVOID generic ACs like "Verify report format matches specifications" - be specific about WHAT format
- GOOD: "Verify clientNumber field contains exactly '17647' in all records"
- BAD: "Verify report contains correct data"
- GOOD: "Verify unitNumber field is exactly 7 digits with leading zeros (format: 0XXXXXX)"
- BAD: "Verify data fields are correct"

FORMAT:
1. Summary: '[Epic Name] - Testing - [Area]'
2. Description with bold headers:
   **Background** - Why this ticket exists
   **Test Scope** - What's tested (include specific field names if available)
   **Source Requirements** - List child tickets (KEY-X: Summary)
3. AC: Create ONE acceptance criterion per distinct requirement/field/constraint ("Verify...", "Confirm...")
   - Number of ACs should match the actual requirements (1 AC for simple tickets, 15+ ACs for complex ones)
   - Each AC tests a specific, independent aspect
   - Manual testable, no technical details
   - Reference specific fields, formats, and constraints when available
   - Be precise and measurable

JSON OUTPUT:
{
  "summary": "[Epic] - Testing - [Area]",
  "description": "**Background**\\n\\n[Why]\\n\\n**Test Scope**\\n\\n[What - with specific fields if available]\\n\\n**Source Requirements**\\n\\n- KEY-1: Summary",
  "acceptance_criteria": ["Verify [specific field/aspect]...", "Confirm [specific constraint]..."],
  "child_tickets": [{"key": "KEY-1", "summary": "..."}]
}

IMPORTANT DATA HANDLING:
- Focus on functional requirements and test scenarios only
- Do NOT generate, request, or repeat specific user identities (names, emails, usernames)
- Do NOT generate or request sensitive internal data (credentials, API keys, secrets)
- If input contains potentially sensitive data, reference it generically without repeating verbatim
- Prioritize test coverage and quality over metadata"""

    def _get_refinement_system_prompt(self) -> str:
        return """Senior BA improving rejected test ticket.

Fix issues while keeping:
- Author's style
- **Background**, **Test Scope**, **Source Requirements**
- One AC per requirement/field/constraint ("Verify...", "Confirm...")
- Exclude out-of-scope

JSON: Same format as generation.

IMPORTANT DATA HANDLING:
- Focus on functional requirements and test scenarios only
- Do NOT generate, request, or repeat specific user identities (names, emails, usernames)
- Do NOT generate or request sensitive internal data (credentials, API keys, secrets)
- If input contains potentially sensitive data, reference it generically without repeating verbatim
- Prioritize test coverage and quality over metadata"""

    def _build_generation_prompt(self, epic_name: str, functional_area: str,
                                 child_tickets: List[Dict], epic_context: Dict) -> str:
        print(f"DEBUG TestTicketGen: _build_generation_prompt called")
        print(f"DEBUG TestTicketGen: epic_context keys: {list(epic_context.keys())}")
        print(f"DEBUG TestTicketGen: epic_context has epic_attachments: {'epic_attachments' in epic_context}")
        if 'epic_attachments' in epic_context:
            print(f"DEBUG TestTicketGen: epic_attachments count in context: {len(epic_context['epic_attachments'])}")

        epic_desc = epic_context.get('epic_desc', '')
        epic_desc_cleaned = clean_jira_text_for_llm(epic_desc) if epic_desc else ''
        # Sanitize epic content to prevent prompt injection
        epic_name_safe = sanitize_prompt_input(epic_name)
        epic_desc_safe = sanitize_prompt_input(epic_desc_cleaned) if epic_desc_cleaned else ''

        child_context = "\n\nChild Tickets:\n"
        for child in child_tickets[:20]:
            key = child.get('key', '')
            summary = child.get('summary', '')
            desc = child.get('desc', '')
            # Sanitize user-provided content to prevent prompt injection
            summary_safe = sanitize_prompt_input(summary) if summary else ''
            desc_cleaned = clean_jira_text_for_llm(desc) if desc else ''
            desc_safe = sanitize_prompt_input(desc_cleaned) if desc_cleaned else ''
            child_context += f"\n{key}: {summary_safe}\n"
            if desc_safe:
                child_context += f"  {desc_safe[:300]}...\n"

        # Format attachments
        print(f"DEBUG TestTicketGen: About to call _format_attachments")
        attachment_context = self._format_attachments(epic_context)
        print(f"DEBUG TestTicketGen: _format_attachments returned {len(attachment_context)} characters")

        # Sanitize functional_area as well
        functional_area_safe = sanitize_prompt_input(functional_area)

        return f"""Epic: {epic_context.get('epic_key', '')} - {epic_name_safe}

Epic Description:
{epic_desc_safe[:1000]}

{attachment_context}

{child_context}

Create test ticket for '{functional_area_safe}'.
Include Source Tickets section with all relevant child ticket keys.

IMPORTANT INSTRUCTIONS:
1. If there are UI mockups or screenshots attached, create acceptance criteria that test the specific visual/interface aspects shown in those mockups.
2. If attachments contain technical specifications, data formats, or field definitions:
   - Extract SPECIFIC field names (e.g., "clientNumber", "unitNumber", "VIN", "readingDate")
   - Extract EXACT format requirements (e.g., "7 digits with leading zeros", "MM/DD/YYYY", "17 characters")
   - Extract VALUE constraints (e.g., "static value '17647'", "positive whole numbers only", "no decimals")
   - Create acceptance criteria that verify these SPECIFIC requirements
3. Do NOT create generic ACs like "Verify report format is correct" when specific field requirements are available.
4. Be as specific and measurable as possible in your acceptance criteria."""

    def _build_refinement_prompt(self, previous_attempt: str, reviewer_feedback: Dict,
                                epic_name: str, functional_area: str) -> str:
        prompt = f"""PREVIOUS ATTEMPT (REJECTED):
{previous_attempt}

FEEDBACK (Score: {reviewer_feedback.get('quality_score', 0)}/100):
Issues:
"""
        for issue in reviewer_feedback.get('issues', []):
            issue_safe = sanitize_prompt_input(issue) if issue else ''
            prompt += f"- {issue_safe}\n"
        prompt += "\nRecommendations:\n"
        for rec in reviewer_feedback.get('recommendations', []):
            rec_safe = sanitize_prompt_input(rec) if rec else ''
            prompt += f"- {rec_safe}\n"
        functional_area_safe = sanitize_prompt_input(functional_area)
        prompt += f"\n\nCreate improved version for '{functional_area_safe}'."""
        return prompt

    def _format_attachments(self, epic_context: Dict) -> str:
        """
        Format attachments for inclusion in prompt.

        Args:
            epic_context: Epic context containing attachments

        Returns:
            Formatted string representation of attachments
        """
        print(f"DEBUG TestTicketGen: _format_attachments called")
        epic_attachments = epic_context.get('epic_attachments', [])
        child_attachments = epic_context.get('child_attachments', {})
        print(f"DEBUG TestTicketGen: Found {len(epic_attachments)} epic attachments")

        if not epic_attachments and not child_attachments:
            print(f"DEBUG TestTicketGen: No attachments found, returning empty string")
            return ""

        output = ["\nATTACHMENTS:"]

        # Analyze images using vision API
        image_attachments = [att for att in epic_attachments if att.get('type') == 'image']
        print(f"DEBUG TestTicketGen: Found {len(image_attachments)} image attachments")
        print(f"DEBUG TestTicketGen: Has llm attribute: {hasattr(self, 'llm')}")
        print(f"DEBUG TestTicketGen: llm is not None: {self.llm if hasattr(self, 'llm') else 'N/A'}")
        image_analysis = {}

        if image_attachments and hasattr(self, 'llm') and self.llm:
            try:
                print(f"DEBUG TestTicketGen: Analyzing {len(image_attachments)} images for test ticket generation")
                # Analyze images in batches (max 3 at a time)
                for i in range(0, len(image_attachments), 3):
                    batch = image_attachments[i:i+3]
                    analysis = self.llm.analyze_images(
                        batch,
                        "UI mockups and screenshots for test ticket generation. Describe specific UI elements, buttons, forms, charts, tables, filters, and interactions visible that need testing."
                    )
                    # Store analysis for each image in the batch
                    for att in batch:
                        image_analysis[att.get('filename')] = analysis
                print(f"DEBUG TestTicketGen: Vision analysis returned {len(image_analysis)} image descriptions")
            except Exception as e:
                print(f"DEBUG TestTicketGen: Failed to analyze images: {e}")

        # Epic attachments
        if epic_attachments:
            for att in epic_attachments:
                filename = att.get('filename', 'Unknown')
                att_type = att.get('type', 'unknown')

                if att_type == 'image':
                    output.append(f"  • {filename} - UI Mockup/Screenshot")
                    if filename in image_analysis:
                        # Include the full vision analysis for test ticket generation
                        output.append(f"    AI Vision Analysis:\n    {image_analysis[filename]}")
                    else:
                        output.append(f"    → Showing visual/UI requirements that should be tested")
                elif att_type == 'document':
                    content = att.get('content', '')
                    # Include full document content for detailed test ticket generation
                    # (truncate only if extremely large to avoid token overflow)
                    max_chars = 10000  # Allow up to ~10k characters per document
                    doc_content = content[:max_chars] + "..." if len(content) > max_chars else content
                    output.append(f"  • {filename} - Document")
                    if doc_content:
                        output.append(f"    Full content:\n    {doc_content}")

        # Child ticket attachments (only show images for UI testing)
        ui_mockups_count = 0
        if child_attachments:
            for child_key, attachments in child_attachments.items():
                for att in attachments:
                    if att.get('type') == 'image':
                        ui_mockups_count += 1
                        filename = att.get('filename', 'Unknown')
                        output.append(f"  • {child_key}/{filename} - UI Mockup/Screenshot")

        if ui_mockups_count > 0 or image_attachments:
            total_images = ui_mockups_count + len(image_attachments)
            output.append(f"\n  → TOTAL: {total_images} UI mockups/screenshots found")
            output.append("  → CRITICAL: Create detailed acceptance criteria to verify specific UI elements, buttons, forms, charts, filters, and interactions shown in the mockups above")

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
                pydantic_model=TestTicketResponse
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
