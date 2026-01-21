"""
E2E Consolidator Agent - Creates functional area E2E test tickets

This agent:
- Extracts ALL acceptance criteria from all test tickets
- Groups ACs by functional area (Data Sync, Error Handling, Validation, etc.)
- Creates ONE E2E ticket per functional area with detailed, preserved ACs
- Ensures no detail is lost - ACs are merged only when duplicated
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from pydantic import BaseModel, Field
from .base_agent import BaseAgent


class DetailedAC(BaseModel):
    """Schema for a detailed acceptance criterion with source tracking"""
    criterion: str = Field(description="The specific, detailed acceptance criterion - preserve ALL field names, formats, and validation rules")
    source_tickets: List[str] = Field(description="Ticket IDs this AC came from (may be multiple if merged)")


class E2EScenario(BaseModel):
    """Schema for an E2E test scenario within a functional area"""
    scenario_name: str = Field(description="Name of the E2E scenario")
    description: str = Field(description="What this scenario validates")
    user_journey: List[str] = Field(description="Step-by-step user journey (5-10 specific steps)")
    covered_acs: List[int] = Field(description="Indices of acceptance_criteria this scenario covers (0-based)")


class FunctionalAreaE2ETicket(BaseModel):
    """Schema for a single functional area E2E ticket"""
    functional_area: str = Field(description="Name of the functional area (e.g., 'Data Synchronization', 'Error Handling', 'Validation', 'Configuration')")
    summary: str = Field(description="Ticket summary: '[Epic Key] E2E - [Functional Area]'")
    description: str = Field(description="Description of what this functional area E2E ticket covers")
    acceptance_criteria: List[DetailedAC] = Field(description="ALL detailed acceptance criteria for this area - preserve every specific detail")
    scenarios: List[E2EScenario] = Field(description="2-3 E2E scenarios for this functional area")
    source_tickets: List[str] = Field(description="All source ticket IDs that contributed to this functional area")


class FunctionalAreaE2EResponse(BaseModel):
    """Response schema containing multiple functional area E2E tickets"""
    functional_areas: List[FunctionalAreaE2ETicket] = Field(description="List of E2E tickets, one per functional area")
    total_acs_extracted: int = Field(description="Total number of ACs extracted from source tickets")
    total_acs_after_merge: int = Field(description="Total ACs after merging duplicates (should be close to total_acs_extracted)")


class E2EConsolidatorAgent(BaseAgent):
    """
    Creates functional area E2E test tickets by extracting and grouping ACs
    """

    def __init__(self, llm):
        super().__init__(llm)

    def consolidate_e2e_tickets(
        self,
        epic_data: Dict[str, Any],
        all_test_tickets: List[Dict[str, Any]],
        existing_e2e_tickets: List[Dict[str, Any]],
        generated_ticket_ids: List[str] = None,
        use_structured_output: bool = True
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Create multiple functional area E2E tickets from all test tickets

        Args:
            epic_data: Epic information
            all_test_tickets: All test tickets (generated + existing)
            existing_e2e_tickets: Existing E2E test tickets found (for reference)
            generated_ticket_ids: List of ticket IDs that were newly generated
            use_structured_output: Whether to use structured output

        Returns:
            Tuple of (e2e_response_data, error_message)
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            epic_data,
            all_test_tickets,
            existing_e2e_tickets,
            generated_ticket_ids or []
        )

        # Count total ACs
        total_acs = sum(len(t.get('acceptance_criteria', [])) for t in all_test_tickets)
        print(f"DEBUG E2E Consolidator: Sending {len(all_test_tickets)} tickets with {total_acs} total ACs for functional area grouping")

        # Issue 2.1 Fix: Handle zero acceptance criteria case
        if total_acs == 0:
            error_msg = "Cannot create E2E tickets: No acceptance criteria found in source tickets. Please ensure test tickets have acceptance criteria defined."
            print(f"WARNING E2E Consolidator: {error_msg}")
            return None, error_msg

        if use_structured_output:
            result, error = self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=12000  # Increased for multiple tickets
            )

            if error:
                return None, error

            return result, None
        else:
            # Fallback to regular JSON mode
            result, error = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=12000
            )

            if error:
                return None, error

            # Parse JSON response
            e2e_data = self._parse_json_response(result)
            if not e2e_data:
                return None, "Failed to parse E2E consolidation response"

            return e2e_data, None

    # Keep old method for backwards compatibility
    def consolidate_e2e_ticket(
        self,
        epic_data: Dict[str, Any],
        all_test_tickets: List[Dict[str, Any]],
        existing_e2e_tickets: List[Dict[str, Any]],
        generated_ticket_ids: List[str] = None,
        use_structured_output: bool = True
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Backwards compatible method - now calls consolidate_e2e_tickets"""
        return self.consolidate_e2e_tickets(
            epic_data,
            all_test_tickets,
            existing_e2e_tickets,
            generated_ticket_ids,
            use_structured_output
        )

    def _build_system_prompt(self) -> str:
        """System prompt for Functional Area E2E Consolidator"""
        return """You are an Expert QA Architect specializing in End-to-End (E2E) test design.

YOUR MISSION:
Create MULTIPLE E2E test tickets, one for each FUNCTIONAL AREA, by extracting and grouping ALL acceptance criteria from the source tickets.

CRITICAL RULES - READ CAREFULLY:

1. EXTRACT ALL ACs: Every single acceptance criterion from every source ticket MUST be captured
2. PRESERVE ALL DETAILS: Never summarize or abstract away specific details
   - Keep exact field names (e.g., 'VIN', 'unitNumber', 'licenseNumber')
   - Keep exact formats (e.g., '17 characters', '7 digits with leading zeros', 'YYYY-MM-DD')
   - Keep exact validation rules (e.g., 'alphanumeric only', 'must not be null')
   - Keep exact thresholds (e.g., 'within 5 minutes', 'retry 3 times')
3. **EXTRACT SPECIFIC API ENDPOINTS**: When source tickets mention API endpoints, PRESERVE EXACT endpoint paths:
   - Keep exact HTTP methods and paths (e.g., 'POST /pending', 'GET /pending?customerId=X&status=PENDING')
   - Keep exact query parameters and path variables
   - Keep exact request/response field names
   - Example: "Verify POST /pending endpoint creates a PENDING row" NOT "Verify the API creates a record"
4. **EXTRACT SPECIFIC DB SCHEMA**: When source tickets mention database tables/fields, PRESERVE EXACT names:
   - Keep exact table names (e.g., 'PendingChange', 'pending_changes')
   - Keep exact column names (e.g., 'customerId', 'entityType', 'status', 'correlationId')
   - Keep exact data types (e.g., 'JSON', 'VARCHAR', 'TIMESTAMP')
   - Keep exact constraints (e.g., 'status=PENDING', 'NOT NULL')
   - Example: "Verify PendingChange table has 'customerId', 'entityType', 'diff', 'status' fields" NOT "Verify database record is created"
5. MERGE ONLY DUPLICATES: Only merge ACs if they are truly saying the same thing
   - If two ACs mention different fields, keep them separate
   - If two ACs have different validation rules, keep them separate
   - When merging, combine ALL details from both ACs into one comprehensive AC

FUNCTIONAL AREAS TO IDENTIFY:
Analyze the ACs and group them into logical functional areas such as:
- Data Synchronization (create, update, delete operations)
- Data Mapping & Transformation (field mappings, format conversions)
- Error Handling & Logging (error codes, retry logic, alerts)
- Validation & Business Rules (field validation, constraints)
- Configuration & Settings (customer-specific settings, authentication)
- Reporting & Notifications (email alerts, reports)
- Integration & API (API calls, webhooks, external systems, service integrations)
  - Include: API endpoint verification - USE SPECIFIC endpoint names from requirements (e.g., "/api/users", "POST /orders")
  - Include: Request/response field validation - USE SPECIFIC field names (e.g., "verify response contains 'userId', 'email', 'status'")
  - Include: Error handling with SPECIFIC status codes (e.g., "verify 400 Bad Request", "verify 401 Unauthorized")
  - Include: Authentication checks, timeout scenarios, retry logic
- Database Validation & Data Integrity (database operations, data persistence, audit trails)
  - Include: Record verification - USE SPECIFIC table names from requirements (e.g., "'users' table", "'orders' table")
  - Include: Field validation - USE SPECIFIC column names (e.g., "verify 'status' field", "check 'created_at' timestamp")
  - Include: Data relationship checks with SPECIFIC foreign keys (e.g., "'order_items.order_id' references 'orders.id'")
  - Include: Audit log verification with SPECIFIC fields (e.g., "'action', 'entity_id', 'user_id', 'timestamp'")

You may identify 3-7 functional areas depending on the source tickets' scope.

OUTPUT STRUCTURE:

For EACH functional area, create an E2E ticket with:

1. functional_area: Clear name (e.g., "Data Synchronization")
2. summary: "[Epic Key] E2E - [Functional Area Name]"
3. description: 2-3 sentences about what this area covers
4. acceptance_criteria: List of DetailedAC objects:
   - criterion: The FULL, SPECIFIC acceptance criterion (no summarization!)
   - source_tickets: Which ticket(s) this AC came from
5. scenarios: 2-3 E2E user journey scenarios for this area
6. source_tickets: All ticket IDs that contributed ACs to this area

SCENARIO FORMAT:
- scenario_name: Business-focused name
- description: What the scenario validates
- user_journey: 5-10 SPECIFIC steps (include exact field names, buttons, values)
  - UI steps: "Navigate to [page]", "Click [button]", "Enter [value] in [field]"
  - API steps: "Send request to the API endpoint", "Verify API returns expected response"
  - DB steps: "Query the database to verify the record", "Verify database entry is created/updated"
- covered_acs: Which AC indices (0-based) this scenario tests

EXAMPLE E2E SCENARIO WITH API/DB VERIFICATION (use specific names from requirements):
{
  "scenario_name": "Complete User Registration Flow",
  "description": "Validates user registration from UI through API to database persistence",
  "user_journey": [
    "Navigate to /register page",
    "Enter 'email', 'password', 'firstName', 'lastName' in the registration form",
    "Click 'Create Account' button",
    "Verify success message 'Account created successfully' displayed",
    "Send GET request to /api/users/{id} endpoint",
    "Verify API returns 200 OK with 'userId', 'email', 'status'='active' fields",
    "Query 'users' table for the new record",
    "Verify record exists with 'email', 'password_hash', 'created_at', 'status'='active'",
    "Query 'audit_log' table for registration entry",
    "Verify entry with 'action'='USER_CREATED', 'entity_type'='user', 'timestamp'"
  ],
  "covered_acs": [0, 1, 5, 8]
}

EXAMPLES OF CORRECT AC PRESERVATION:

Source AC: "Verify that the VIN field accepts exactly 17 alphanumeric characters"
CORRECT output: "Verify that the VIN field accepts exactly 17 alphanumeric characters"
WRONG output: "Verify vehicle identifier format" (too vague!)

Source AC 1: "Verify driver firstName is synchronized"
Source AC 2: "Verify driver lastName is synchronized"
CORRECT output (if merging): "Verify driver fields are synchronized: 'firstName', 'lastName'"
WRONG output: "Verify driver data syncs" (lost the field names!)

Source AC: "System retries failed sync up to 3 times with 30-second delay"
CORRECT output: "System retries failed sync up to 3 times with 30-second delay"
WRONG output: "System has retry logic" (lost the specifics!)

**API ENDPOINT EXAMPLES**:
Source AC: "Given an Element delta is posted to POST /pending, then a PENDING row exists with diff and currentSnapshot captured"
CORRECT output: "Verify POST /pending endpoint creates a PENDING row with 'diff' and 'currentSnapshot' fields populated"
WRONG output: "Verify API creates pending record" (lost endpoint path and field names!)

Source AC: "GET /pending?customerId=X&status=PENDING returns only matching items"
CORRECT output: "Verify GET /pending?customerId=X&status=PENDING returns only items matching the customerId and status filters"
WRONG output: "Verify listing API returns filtered results" (lost the exact endpoint and query params!)

**DATABASE SCHEMA EXAMPLES**:
Source AC: "PendingChange { id, customerId, entityType, entityId, sourceSystem, proposedPayload(JSON), currentSnapshot(JSON|null), diff(JSON), status=PENDING }"
CORRECT output: "Verify PendingChange table contains fields: 'id', 'customerId', 'entityType', 'entityId', 'sourceSystem', 'proposedPayload' (JSON), 'currentSnapshot' (JSON|null), 'diff' (JSON), 'status' (default=PENDING)"
WRONG output: "Verify pending changes are stored in database" (lost all schema details!)

Source AC: "Posting the identical normalized payload (same checksum) returns the existing record (no duplicate row)"
CORRECT output: "Verify idempotent ingest: POST with identical 'checksum' value returns existing record without creating duplicate row"
WRONG output: "Verify no duplicates are created" (lost the checksum detail!)

QUALITY CHECKLIST:
- [ ] Every AC from source tickets appears in exactly one functional area
- [ ] No field names, formats, or rules have been lost
- [ ] No API endpoint paths have been summarized (keep exact paths like 'POST /pending', 'GET /pending?customerId=X')
- [ ] No database table/column names have been summarized (keep exact names like 'PendingChange', 'customerId', 'entityType')
- [ ] Each functional area has 5-15 detailed ACs (more is fine!)
- [ ] Each scenario has specific user journey steps with real values
- [ ] source_tickets accurately lists which tickets contributed

REMEMBER: The E2E tickets will be used to generate test cases. Vague ACs = useless test cases. Specific ACs = valuable test cases."""

    def _build_user_prompt(
        self,
        epic_data: Dict[str, Any],
        all_test_tickets: List[Dict[str, Any]],
        existing_e2e_tickets: List[Dict[str, Any]],
        generated_ticket_ids: List[str] = None
    ) -> str:
        """Build user prompt with ALL ACs clearly listed for grouping"""
        epic_key = epic_data.get('key', '')
        epic_summary = epic_data.get('summary', '')
        epic_description = epic_data.get('description', '')
        generated_ids = set(generated_ticket_ids or [])

        # Count total ACs
        total_acs = 0
        for ticket in all_test_tickets:
            total_acs += len(ticket.get('acceptance_criteria', []))

        prompt = f"""Create FUNCTIONAL AREA E2E TICKETS for this epic:

EPIC: {epic_key} - {epic_summary}

EPIC DESCRIPTION:
{epic_description[:1500]}

════════════════════════════════════════════════════════════════════════════════
IMPORTANT: You MUST extract and preserve ALL {total_acs} acceptance criteria below.
Group them by functional area and create one E2E ticket per area.
DO NOT summarize or lose any details!
════════════════════════════════════════════════════════════════════════════════

"""
        # List ALL tickets with ALL their ACs
        ticket_num = 0
        for ticket in all_test_tickets:
            ticket_num += 1
            ticket_id = ticket.get('id', f'TICKET-{ticket_num}')
            summary = ticket.get('summary', 'No summary')
            acs = ticket.get('acceptance_criteria', [])
            is_generated = ticket_id in generated_ids or ticket.get('ticket_source') == 'generated'
            tag = "[NEW]" if is_generated else "[EXISTING]"

            prompt += f"\n{'─'*80}\n"
            prompt += f"TICKET {ticket_num}: {tag} {ticket_id}\n"
            prompt += f"Summary: {summary}\n"

            # Include ticket description to capture API endpoints, DB schema, and other technical details
            description = ticket.get('description', '')
            if description:
                # Truncate long descriptions but preserve technical details
                desc_preview = description[:2000] if len(description) > 2000 else description
                prompt += f"Description:\n{desc_preview}\n"

            prompt += f"Acceptance Criteria ({len(acs)}):\n"

            if acs:
                for i, ac in enumerate(acs, 1):
                    prompt += f"  AC-{ticket_num}.{i}: {ac}\n"
            else:
                prompt += f"  (No ACs - use ticket summary/description for coverage)\n"

        # Add existing E2E tickets as reference
        if existing_e2e_tickets:
            prompt += f"\n\n{'═'*80}\n"
            prompt += f"EXISTING E2E TICKETS (for reference - incorporate their coverage):\n"
            prompt += f"{'═'*80}\n"
            for i, e2e_ticket in enumerate(existing_e2e_tickets, 1):
                ticket_key = e2e_ticket.get('id', e2e_ticket.get('key', f'E2E-{i}'))
                summary = e2e_ticket.get('summary', 'No summary')
                prompt += f"\n{i}. {ticket_key}: {summary}\n"

        prompt += f"""

════════════════════════════════════════════════════════════════════════════════
YOUR TASK:
════════════════════════════════════════════════════════════════════════════════

1. EXTRACT all {total_acs} ACs from the tickets above
2. GROUP them into 3-6 functional areas based on what they test
3. CREATE one E2E ticket per functional area with:
   - ALL the ACs for that area (preserve every detail!)
   - 2-3 user journey scenarios
   - References to source tickets

4. ENSURE total_acs_after_merge is close to {total_acs} (only merge true duplicates)

Functional areas to consider:
- Data Synchronization / CRUD Operations
- Data Mapping & Field Transformation
- Error Handling & Retry Logic
- Validation & Business Rules
- Configuration & Customer Settings
- Notifications & Reporting
- Integration Points

Generate the functional_areas array now, ensuring NO AC is lost or summarized."""

        return prompt

    def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 12000
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Call LLM with structured output"""
        response_text, error = self.llm.complete_json(
            system_prompt,
            user_prompt,
            max_tokens=max_tokens,
            pydantic_model=FunctionalAreaE2EResponse
        )

        if error:
            return None, error

        if not response_text:
            return None, "Empty response from LLM"

        # Convert to dict if Pydantic model
        if hasattr(response_text, 'model_dump'):
            result = response_text.model_dump()
        elif isinstance(response_text, str):
            # Parse JSON string
            result = self._parse_json_response(response_text)
            if not result:
                return None, "Failed to parse LLM response as JSON"
        else:
            result = response_text

        return result, None

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 12000
    ) -> Tuple[Optional[str], Optional[str]]:
        """Call LLM in JSON mode"""
        response_text, error = self.llm.complete_json(
            system_prompt,
            user_prompt,
            max_tokens=max_tokens
        )

        return response_text, error

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from LLM"""
        try:
            # Try to parse directly
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try to find any JSON object
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            return None
