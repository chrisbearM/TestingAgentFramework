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
from pydantic import BaseModel, Field
from .base_agent import BaseAgent
from ai_tester.utils.jira_text_cleaner import sanitize_prompt_input


# Pydantic models for structured output
class AcceptanceCriteriaCategory(BaseModel):
    """A category of acceptance criteria"""
    category_name: str = Field(description="Category name (e.g., 'Form Rendering & Data Population', 'Accessibility')")
    criteria: List[str] = Field(description="List of acceptance criteria in this category")

class ImprovedTicket(BaseModel):
    """Schema for the improved ticket"""
    summary: str = Field(description="Enhanced ticket summary matching original author's style")
    description: str = Field(description="Improved description with Background, User Story, Scope, Requirements, and Out of Scope sections. Note: Out of Scope is ONLY included within this description field, not separately.")
    acceptance_criteria_grouped: List[AcceptanceCriteriaCategory] = Field(
        description="Grouped acceptance criteria organized into 4-7 themed categories"
    )
    technical_notes: str = Field(default="", description="Comprehensive technical implementation notes including approach, error handling, security, performance")
    testing_notes: str = Field(default="", description="Testing strategy, browser/device coverage, accessibility testing")
    out_of_scope: List[str] = Field(default_factory=list, description="DEPRECATED: Do not use this field. Out of scope items should only be in the description field under '## Out of Scope' section.")


class Improvement(BaseModel):
    """Schema for a single improvement made"""
    area: str = Field(description="Area that was improved (e.g., 'Acceptance Criteria', 'Description')")
    change: str = Field(description="What was changed")
    rationale: str = Field(description="Why this change improves the ticket")


class TicketImprovementResponse(BaseModel):
    """Complete response schema for ticket improvement"""
    improved_ticket: ImprovedTicket = Field(description="The improved version of the ticket")
    improvements_made: List[Improvement] = Field(description="List of improvements made to the ticket")
    quality_increase: int = Field(description="Estimated quality improvement percentage (0-100)", ge=0, le=100)


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
        epic_context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        use_structured_output: bool = False  # Temporarily disabled until structured outputs are debugged
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Generate an improved version of a ticket

        Args:
            ticket_data: Original ticket (key, summary, description)
            questions: Optional questions from readiness assessment
            epic_context: Optional Epic context for additional information
            model: Optional model override (e.g., 'gpt-4o-mini' for cheaper extraction)
            use_structured_output: Whether to use OpenAI structured outputs (default: True)

        Returns:
            Tuple of (improvement result, error message)
            Result format:
            {
                "improved_ticket": {
                    "summary": "Enhanced summary",
                    "description": "Improved description",
                    "acceptance_criteria": ["Clear AC 1", "Clear AC 2"],
                    "edge_cases": ["Edge case 1"],
                    "error_scenarios": ["Error scenario 1"],
                    "technical_notes": "Optional notes"
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

        if use_structured_output:
            # Use structured output with Pydantic model
            print(f"DEBUG TICKET IMPROVER: Using structured outputs with {TicketImprovementResponse.__name__}")
            print(f"DEBUG TICKET IMPROVER: Model has fields: {list(TicketImprovementResponse.model_fields.keys())}")
            print(f"DEBUG TICKET IMPROVER: ImprovedTicket has fields: {list(ImprovedTicket.model_fields.keys())}")
            # Temporarily disable caching for fresh results
            original_cache_setting = self.llm.cache_client.enabled
            self.llm.cache_client.enabled = False

            result, error = self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=4000,
                model=model
            )

            # Restore original cache setting
            self.llm.cache_client.enabled = original_cache_setting

            if error:
                return None, error

            # result is already a dict from Pydantic model
            # IMPORTANT: Validate and clean up out-of-scope contradictions even for structured output
            result = self._validate_scope_separation(ticket_data, result)

            return result, None
        else:
            # Fallback to regular JSON mode
            # Temporarily disable caching for fresh results
            original_cache_setting = self.llm.cache_client.enabled
            self.llm.cache_client.enabled = False

            result, error = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=4000,
                model=model
            )

            # Restore original cache setting
            self.llm.cache_client.enabled = original_cache_setting

            if error:
                return None, error

            # Parse JSON response
            improvement_data = self._parse_json_response(result)
            if not improvement_data or 'improved_ticket' not in improvement_data:
                return None, "Failed to parse improvement from response"

            # Validate and clean up out-of-scope contradictions
            improvement_data = self._validate_scope_separation(ticket_data, improvement_data)

            # DEBUG: Log what we're returning
            print(f"DEBUG TICKET IMPROVER: Returning improvement_data with keys: {list(improvement_data.keys())}")
            if 'improved_ticket' in improvement_data:
                print(f"DEBUG TICKET IMPROVER: improved_ticket has keys: {list(improvement_data['improved_ticket'].keys())}")

            return improvement_data, None

    def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        model: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Call LLM with structured output using Pydantic model

        Args:
            system_prompt: System prompt defining the agent's role
            user_prompt: User prompt with specific task details
            max_tokens: Maximum tokens for the response
            model: Optional model override

        Returns:
            Tuple of (result dict, error message)
        """
        try:
            result, error = self.llm.complete_json(
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
                model=model,
                pydantic_model=TicketImprovementResponse
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

    def _get_improver_system_prompt(self) -> str:
        """System prompt for Ticket Improver Agent"""
        return """Expert BA improving Jira tickets to SURPASS Atlassian Rovo quality. Goals: Superior organization, comprehensive coverage, testable, accessible.

DESCRIPTION STRUCTURE (Include ALL sections):
## Background
Context and why this work is needed. Link to related tickets/epics.

## User Story
As a [role], I want [feature], so that [benefit]

## Scope
What IS included in this ticket (bullet points)

## Requirements
Detailed functional requirements (bullets or numbered list)

## Out of Scope
What is explicitly NOT included (prevents scope creep)
- Future integrations not in this ticket
- Advanced features for later phases
- Items mentioned but deferred

⚠️ CRITICAL - OUT OF SCOPE PRESERVATION ⚠️
IF the original ticket has an "Out of Scope" section, you MUST:
1. PRESERVE all out-of-scope items EXACTLY as they appear in the original
2. NEVER move out-of-scope items into Requirements, Scope, or Acceptance Criteria
3. NEVER add requirements that enable or implement out-of-scope items
4. NEVER reinterpret out-of-scope functionality as in-scope features

EXAMPLES OF VIOLATIONS (DO NOT DO THIS):
❌ Original out of scope: "Write-backs to Element" → WRONG: Add requirement "Enable one-way write-backs to Element"
❌ Original out of scope: "Backend API integration" → WRONG: Add requirement "Integrate with backend REST API"
❌ Original out of scope: "Advanced search" → WRONG: Add AC "User can perform advanced searches"

If in doubt, KEEP IT OUT OF SCOPE. Scope creep is worse than missing features.

ACCEPTANCE CRITERIA - COMPLETE COVERAGE REQUIREMENT:
⚠️ CRITICAL: EVERY requirement in the Requirements section MUST map to at least one AC

COMPLETENESS CHECKLIST - Apply BEFORE grouping into categories:
1. Read EACH requirement line-by-line from the Requirements section
2. For EACH requirement, create specific ACs covering ALL aspects:
   - Core functionality described
   - ALL specified attributes (required, optional, validation rules, format constraints)
   - ALL UI text content with EXACT wording (labels, messages, tooltips, introduction text)
   - ALL interactive behaviors (hover states, button states, search capabilities, dropdowns)
   - ALL data management rules (session retention, data loss conditions, persistence)
3. Break down compound requirements into separate granular ACs
4. DO NOT summarize or combine related requirements - be exhaustive and explicit
5. Preserve specific wording requirements verbatim (e.g., "Please complete the form below...")

GRANULARITY EXAMPLES - How to break down requirements properly:
❌ BAD (too vague): "Region dropdown validates input"
✅ GOOD (granular): Create THREE separate ACs:
  - "Region field is marked as required and validates that a selection is made"
  - "Region dropdown is populated with a list of available regions"
  - "Region dropdown includes search/filter capability to find regions"

❌ BAD (missing exact text): "Introduction text is visible and correctly formatted"
✅ GOOD (exact wording): "Introduction text displays the exact message: 'Please complete the form below and a Unity expert will be in touch shortly to assist you with your selected solutions.'"

❌ BAD (combined behaviors): "Close button works correctly"
✅ GOOD (separate behaviors): Create TWO separate ACs:
  - "Close button (x) closes the popup while retaining entered data during the session"
  - "Close button displays tooltip text 'Close' on hover"

❌ BAD (missing optional vs required): "Phone number field validates format"
✅ GOOD (explicit requirements): Create TWO separate ACs:
  - "Phone number field is optional and does NOT prevent form submission when empty"
  - "Phone number field validates basic mobile number format when populated"

❌ BAD (vague button state): "Send button activates when fields are filled"
✅ GOOD (explicit states): Create TWO separate ACs:
  - "Send button is deactivated/disabled by default when form first loads"
  - "Send button becomes active/enabled only when ALL required fields are filled with valid data"

ACCEPTANCE CRITERIA - GROUPED BY CATEGORY:
After ensuring complete coverage, organize ACs into themed sections based on ticket type.

Common categories (choose 4-7 that apply):

For UI/Form Tickets:
  "Form Rendering & Data Population"
  "Field Validation"
  "User Interactions & Button States"
  "Session/State Management"
  "Edge Cases & Error Scenarios"
  "Accessibility"

For API Tickets:
  "Request Handling"
  "Response Format & Data"
  "Authentication & Authorization"
  "Error Handling"
  "Performance & Rate Limiting"
  "Edge Cases & Error Scenarios"

For Integration Tickets:
  "Data Flow & Mapping"
  "Error Handling & Rollback"
  "Monitoring & Logging"
  "Edge Cases & Error Scenarios"

ALWAYS include "Accessibility" category if UI involved:
- Keyboard navigation (tab order, enter/escape)
- Screen reader support (ARIA labels, semantic HTML)
- Focus indicators visible
- Error announcements for assistive tech

ALWAYS include "Edge Cases & Error Scenarios" category:
- Invalid/incomplete input handling
- Empty/null data scenarios
- Network failures, timeouts
- Browser/storage unavailable
- Concurrent operations
- Large data sets

AC WRITING FORMAT - Match original style EXACTLY:
⚠️ CRITICAL: Analyze the original ticket's AC format and use THAT SAME format!
- If original uses bullet points, use bullet points
- If original uses numbered list, use numbered list
- If original uses "System shall...", use "System shall..."
- If original uses descriptive statements "The report includes...", use that style
- If original uses imperative "Verify that...", use that style
Use ONE consistent format within each category - the format from the ORIGINAL ticket.

TECHNICAL NOTES (Comprehensive):
Include 7-10 specific points covering:
- Implementation approach (libraries, frameworks, patterns to use)
- Data storage/state management strategy
- Error handling approach (try-catch, error boundaries, user feedback)
- Future extensibility (how to add features later)
- Security/privacy implications (data handling, PII, compliance)
- Performance considerations (optimization, caching, debouncing)
- Browser/platform compatibility requirements
- Code organization (folder structure, naming conventions)

TESTING NOTES (MUST be ticket-specific):
⚠️ CRITICAL: Testing notes must be SPECIFIC to this ticket's functionality, NOT generic testing advice
- Identify the SPECIFIC features/functionality being implemented in THIS ticket
- List CONCRETE test scenarios relevant to THIS ticket's requirements
- Include SPECIFIC edge cases for THIS ticket's domain/data/operations
- Only mention UI/browser testing if the ticket involves UI changes
- Only mention accessibility if the ticket has user-facing components
- Focus on integration points, data validation, error scenarios specific to THIS ticket
EXAMPLES:
- Backend API: "Test sync with 2000+ vehicle records", "Verify handling of invalid Element API responses"
- UI Feature: "Test form with all required fields populated", "Verify error messages display for invalid email"
- Data Processing: "Test import with malformed CSV", "Verify deduplication logic with duplicate records"

JSON STRUCTURE:
{
  "improved_ticket": {
    "summary": "Enhanced summary in original style",
    "description": "## Background\\n...\\n## User Story\\n...\\n## Scope\\n...\\n## Requirements\\n...\\n## Out of Scope\\n- Backend submission to Salesforce\\n- Persistent storage beyond session\\n- International phone number formats",
    "acceptance_criteria_grouped": [
      {
        "category_name": "Form Rendering & Data Population",
        "criteria": [
          "The popup form displays all specified fields",
          "Interested In list is populated from list builder"
        ]
      },
      {
        "category_name": "Field Validation",
        "criteria": [
          "Required fields are visually indicated",
          "Email field validates standard format"
        ]
      },
      {
        "category_name": "Accessibility",
        "criteria": [
          "All form fields accessible via keyboard navigation",
          "Labels associated with inputs for screen readers"
        ]
      }
    ],
    "technical_notes": "- Use React Hook Form for validation\\n- Store in sessionStorage (not localStorage)\\n- Implement debounced email validation\\n- Prepare for Salesforce integration\\n- Ensure no PII persisted beyond session\\n- Use ARIA labels for accessibility\\n- Handle storage unavailable gracefully",
    "testing_notes": "- Test form submission with all fields populated correctly\\n- Verify validation triggers for required fields (First Name, Last Name, Email)\\n- Test email field with invalid formats (missing @, invalid domain)\\n- Verify Interested In dropdown populated from list builder data\\n- Test form behavior when sessionStorage is unavailable\\n- Verify keyboard-only navigation through all form fields\\n- Test Cancel button clears form but retains data in session\\n- Verify Submit button disabled until all required fields valid",
    "out_of_scope": []
  },
  "improvements_made": [{"area": "AC Organization", "change": "Grouped into 6 categories", "rationale": "Easier to scan and organize testing"}],
  "quality_increase": 85
}

CRITICAL - OUT OF SCOPE HANDLING:
⚠️ CRITICAL: Do NOT make up or infer out-of-scope items!
- ONLY include out-of-scope items if the original ticket EXPLICITLY mentions them
- If the original ticket has NO out-of-scope section or items, write "## Out of Scope\\nNone" in the description
- Do NOT carry over out-of-scope items from previous tickets
- Do NOT invent plausible-sounding out-of-scope items
- Do NOT populate the separate "out_of_scope" array field - ALWAYS leave it empty []
EXAMPLES:
- Original has out-of-scope: description contains "## Out of Scope\\n- Write-backs to Element\\n- Real-time sync"
- Original has NO out-of-scope: description contains "## Out of Scope\\nNone"
- Always: out_of_scope: []

IMPORTANT DATA HANDLING:
- Focus on functional requirements and test scenarios only
- Do NOT generate, request, or repeat specific user identities (names, emails, usernames)
- Do NOT generate or request sensitive internal data (credentials, API keys, secrets)
- If input contains potentially sensitive data, reference it generically without repeating verbatim
- Prioritize test coverage and quality over metadata

CRITICAL - TICKET SPECIFICITY:
⚠️ Each ticket improvement is COMPLETELY INDEPENDENT - forget everything from previous tickets!
- ALL content MUST be specific to THIS ticket only
- Out of Scope: If original ticket has NO out-of-scope items, write "None" - do NOT make up items
- Do NOT include out of scope items from other tickets or unrelated features
- Testing Notes MUST be specific to THIS ticket only, NOT from previous tickets
- Technical Notes MUST be specific to THIS ticket only, NOT from previous tickets
- Do NOT carry over ANY content from previous ticket improvements
- Treat each ticket improvement request as if it's the first ticket you've ever seen
- There is NO context or memory between ticket improvement requests"""

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

        # Sanitize all user-provided content to prevent prompt injection
        summary_safe = sanitize_prompt_input(ticket_data.get('summary', 'N/A'))
        description_safe = sanitize_prompt_input(ticket_data.get('description', 'No description provided'))
        acceptance_criteria_safe = sanitize_prompt_input(ticket_data.get('acceptance_criteria', 'No acceptance criteria provided'))

        prompt = f"""CRITICAL: This is a NEW, INDEPENDENT ticket improvement request. Do NOT use any content from previous tickets.

Analyze and improve the following Jira ticket to SURPASS Atlassian Rovo quality:

**Original Ticket**: {ticket_data.get('key', 'N/A')}
**Summary**: {summary_safe}

**Description**:
{description_safe}

**Original Acceptance Criteria** (if present):
{acceptance_criteria_safe}

{epic_text}
{questions_text}

CRITICAL REMINDER:
- ALL content must be derived ONLY from the ticket information above
- Do NOT reuse Testing Notes, Technical Notes, or Out of Scope items from any previous tickets
- This is a fresh, independent analysis of THIS specific ticket

TASK: Create a superior improved version with:

1. **DESCRIPTION** - All 5 sections:
   - Background (context, why needed)
   - User Story (As a/I want/so that)
   - Scope (what IS included - bullets)
   - Requirements (detailed functional requirements)
   - Out of Scope (what is NOT included)

   ⚠️  CRITICAL: If original ticket has "Out of Scope" items:
   1. COPY the entire "Out of Scope" section VERBATIM from original ticket
   2. Do NOT modify, expand, or interpret out-of-scope items
   3. Do NOT add requirements that implement out-of-scope functionality
   4. When in doubt, preserve the original out-of-scope section exactly as-is

2. **ACCEPTANCE CRITERIA** - Grouped into 4-7 themed categories:
   - Identify ticket type (UI/Form, API, Integration, etc.)
   - Choose relevant category names from system prompt
   - ALWAYS include "Accessibility" if UI involved
   - ALWAYS include "Edge Cases & Error Scenarios"
   - Group related ACs under each category
   - Maintain consistent AC format within each category (match original style)

3. **TECHNICAL NOTES** - Comprehensive (7-10 points):
   - Implementation approach
   - Data storage/state management
   - Error handling
   - Future extensibility
   - Security/privacy
   - Performance
   - Browser compatibility

4. **TESTING NOTES** - Detailed testing strategy:
   - Test types (manual, automated, integration)
   - Browser coverage
   - Device/viewport coverage
   - Accessibility testing
   - Edge case testing

5. **OUT OF SCOPE** - Explicit exclusions:
   - Items mentioned but not in this ticket
   - Future integrations
   - Advanced features for later

CRITICAL STYLE MATCHING - HIGHEST PRIORITY:
⚠️ Style matching is MORE IMPORTANT than any format preference!
- FIRST: Analyze the original ticket's writing style in detail:
  * Does it use bullet points or numbered lists?
  * Does it use "System shall" or descriptive statements like "The report includes..."?
  * Is it formal technical ("System shall") or business-oriented ("Customers can...")?
  * What verb forms does it use (imperative, declarative, modal)?
- THEN: Match that EXACT style in your improved version
- Do NOT impose "System shall" format if original doesn't use it
- Do NOT change bullet points to numbers if original uses bullets
- Preserve the author's voice, terminology, and phrasing patterns

EXAMPLES OF STYLE MATCHING:
✓ Original uses bullets "• The report includes...", Improved uses bullets "• The report includes..."
✗ Original uses bullets "• The report includes...", Improved uses "System shall include..."
✓ Original uses "Customers can...", Improved uses "Customers can..."
✗ Original uses "Customers can...", Improved uses "System shall allow customers to..."

Return ONLY the JSON response."""

        return prompt

    def _validate_scope_separation(
        self,
        original_ticket: Dict[str, Any],
        improvement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and PRESERVE out-of-scope items from original ticket.
        If the original has an "Out of Scope" section, ensure it's preserved in the improved version.

        Args:
            original_ticket: Original ticket data
            improvement_data: LLM-generated improvement

        Returns:
            Cleaned improvement_data with original out-of-scope section preserved
        """
        original_desc = original_ticket.get('description', '')
        improved_ticket = improvement_data.get('improved_ticket', {})
        improved_desc = improved_ticket.get('description', '')

        # Write full ticket data to debug file for inspection
        with open('debug_validation.log', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"VALIDATION RUN for ticket: {original_ticket.get('key', 'unknown')}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Original ticket keys: {list(original_ticket.keys())}\n")
            f.write(f"Original description type: {type(original_desc)}\n")
            f.write(f"Original description length: {len(original_desc)}\n")
            f.write(f"Original description first 500 chars:\n{original_desc[:500]}\n")
            f.write(f"\n")

        # Check if original ticket has an "Out of Scope" section (case-insensitive)
        original_lower = original_desc.lower()
        if 'out of scope' not in original_lower:
            print("DEBUG VALIDATION: No 'out of scope' found in original ticket", flush=True)
            with open('debug_validation.log', 'a', encoding='utf-8') as f:
                f.write(f"[X] NO 'out of scope' found in original description\n")
            return improvement_data  # No out-of-scope section to preserve

        # Find the position of "Out of Scope" in original
        out_of_scope_pos = original_lower.find('out of scope')
        print(f"DEBUG VALIDATION: Found 'out of scope' at position {out_of_scope_pos}", flush=True)
        print(f"DEBUG VALIDATION: Original description length: {len(original_desc)}", flush=True)

        # Write to debug file
        with open('debug_validation.log', 'a', encoding='utf-8') as f:
            f.write(f"\n=== VALIDATION RUN ===\n")
            f.write(f"Original ticket key: {original_ticket.get('key', 'unknown')}\n")
            f.write(f"Found 'out of scope' at position: {out_of_scope_pos}\n")
            f.write(f"Original description length: {len(original_desc)}\n")

        # Extract the original out-of-scope content
        # Look for the end of this section by finding common section markers
        section_markers = ['\nValue:', '\nUnsorted Remarks:', '\nScope Includes:',
                          '\n##', '\nAcceptance Criteria:', '\nNotes:',
                          '\nTechnical Notes:', '\nAssumptions:']

        # Start searching after "Out of Scope:"
        search_start = out_of_scope_pos + len('out of scope')
        next_section_pos = -1

        for marker in section_markers:
            pos = original_desc.find(marker, search_start)
            if pos > 0 and (next_section_pos == -1 or pos < next_section_pos):
                next_section_pos = pos
                print(f"DEBUG VALIDATION: Found next section marker '{marker}' at position {pos}")

        if next_section_pos == -1:
            # No next section found, take everything till end
            original_out_of_scope_content = original_desc[search_start:].strip()
            print("DEBUG VALIDATION: No next section marker found, taking rest of description")
        else:
            # Extract content between "Out of Scope:" and next section
            original_out_of_scope_content = original_desc[search_start:next_section_pos].strip()
            print(f"DEBUG VALIDATION: Extracted content from {search_start} to {next_section_pos}")

        # Clean up the content - remove leading colon if present
        if original_out_of_scope_content.startswith(':'):
            original_out_of_scope_content = original_out_of_scope_content[1:].strip()

        print(f"DEBUG VALIDATION: Extracted out-of-scope content: '{original_out_of_scope_content[:100]}...'", flush=True)
        print(f"DEBUG VALIDATION: Full extracted content length: {len(original_out_of_scope_content)}", flush=True)

        # Write extracted content to debug file
        with open('debug_validation.log', 'a', encoding='utf-8') as f:
            f.write(f"Extracted out-of-scope content:\n{original_out_of_scope_content}\n")
            f.write(f"Content length: {len(original_out_of_scope_content)}\n")

        # Now check if improved description has an Out of Scope section
        improved_lower = improved_desc.lower()
        improved_out_pos = improved_lower.find('## out of scope')

        print(f"DEBUG VALIDATION: Looking for '## out of scope' in improved description")
        print(f"DEBUG VALIDATION: Found improved out-of-scope at position: {improved_out_pos}")

        if improved_out_pos >= 0:
            # Find where the improved out-of-scope section ends (next ## heading)
            next_improved_section = improved_desc.find('\n##', improved_out_pos + 15)
            print(f"DEBUG VALIDATION: Next section in improved starts at: {next_improved_section}")

            if next_improved_section == -1:
                # Out of scope is last section
                new_desc = improved_desc[:improved_out_pos] + '## Out of Scope\n' + original_out_of_scope_content
            else:
                # Replace the section, keeping what comes after
                before = improved_desc[:improved_out_pos]
                after = improved_desc[next_improved_section:]
                new_desc = before + '## Out of Scope\n' + original_out_of_scope_content + '\n\n' + after

            improved_ticket['description'] = new_desc
            improvement_data['improved_ticket'] = improved_ticket
            print(f"SUCCESS VALIDATION: Preserved original 'Out of Scope' section from ticket {original_ticket.get('key', 'unknown')}", flush=True)

            # Write success to debug file
            with open('debug_validation.log', 'a', encoding='utf-8') as f:
                f.write(f"[SUCCESS] Successfully replaced out-of-scope section\n")
        else:
            print("WARNING VALIDATION: Improved ticket doesn't have '## Out of Scope' section - cannot replace!", flush=True)

            # Write warning to debug file
            with open('debug_validation.log', 'a', encoding='utf-8') as f:
                f.write(f"WARNING: Improved ticket doesn't have '## Out of Scope' section!\n")

        return improvement_data
