"""
AI Test Case Generator
Fetches a Jira ticket and generates comprehensive test cases using AI
"""

import os
import json
from dotenv import load_dotenv
from ai_tester import JiraClient, LLMClient
from ai_tester.core.models import TestCase, TestStep, Requirement

# Load environment
load_dotenv()

def critic_review(llm, summary, requirements, test_cases_data):
    """Review test cases for quality and reject nonsensical ones."""
    
    sys_prompt = """You are a Senior QA Manager reviewing test cases.

CRITICAL: Reject test cases that are:
- Nonsensical or don't make logical sense
- Too simplistic (only 1-2 steps when more are needed)
- Don't actually test the requirement
- Repetitive or redundant
- Unrealistic or impossible to execute

Check:
1. Does test case count = requirements × 3?
2. Are tests realistic and executable?
3. Do tests actually test what they claim to test?
4. Are steps detailed enough (3-8 steps per test)?

Return JSON:
{
  "approved": true/false,
  "overall_quality": "excellent"/"good"/"needs_improvement"/"poor",
  "confidence_score": 0-100,
  "issues_found": [
    {"test_case_title": "...", "description": "What's wrong", "suggestion": "How to fix"}
  ],
  "summary": "Brief review summary",
  "recommendation": "Approve or list specific fixes"
}"""
    
    user_prompt = f"""Review these test cases:

REQUIREMENTS ({len(requirements)}):
{json.dumps(requirements, indent=2)}

TEST CASES ({len(test_cases_data)}):
"""
    
    # Group by requirement
    by_req = {}
    for tc in test_cases_data:
        req_id = tc.get("requirement_id", "UNMAPPED")
        by_req.setdefault(req_id, []).append(tc)
    
    for req_id, tcs in by_req.items():
        user_prompt += f"\n{req_id} ({len(tcs)} tests):\n"
        for tc in tcs:
            user_prompt += f"  • [{tc.get('test_type')}] {tc.get('title')} ({len(tc.get('steps', []))} steps)\n"
    
    user_prompt += f"\nExpected: {len(requirements)} × 3 = {len(requirements) * 3} tests\nActual: {len(test_cases_data)} tests"
    
    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=2000)
    
    if error:
        return (None, error)
    
    from ai_tester.utils.utils import safe_json_extract
    return (safe_json_extract(response_text), None)

def generate_test_cases(ticket_key: str):
    """Generate test cases for a Jira ticket using AI."""
    
    print("\n" + "=" * 80)
    print(f"AI TEST CASE GENERATOR - {ticket_key}")
    print("=" * 80)
    
    # Initialize clients
    jira = JiraClient(
        base_url=os.getenv("JIRA_BASE_URL"),
        email=os.getenv("JIRA_EMAIL"),
        api_token=os.getenv("JIRA_API_TOKEN")
    )
    
    llm = LLMClient(enabled=True)
    
    if not llm.enabled:
        print("\n❌ Error: OpenAI API key not found or invalid!")
        print("Please add OPENAI_API_KEY to your .env file")
        return
    
    try:
        # Step 1: Fetch the ticket
        print(f"\n📥 Step 1: Fetching ticket from Jira...")
        issue = jira.get_issue(ticket_key)
        
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        issue_type = fields.get("issuetype", {}).get("name", "")
        
        print(f"   ✅ Found: [{issue_type}] {summary}")
        
        # Get description
        description = fields.get("description", "")
        if isinstance(description, dict):
            from ai_tester.utils.utils import adf_to_plaintext
            description = adf_to_plaintext(description)
        
        # Get acceptance criteria (look in multiple places)
        acceptance_criteria = ""
        
        # Check custom field for acceptance criteria
        for field_key, field_value in fields.items():
            if "acceptance" in field_key.lower() or "criteria" in field_key.lower():
                if isinstance(field_value, str):
                    acceptance_criteria = field_value
                elif isinstance(field_value, dict):
                    from ai_tester.utils.utils import adf_to_plaintext
                    acceptance_criteria = adf_to_plaintext(field_value)
        
        print(f"\n📝 Ticket Info:")
        print(f"   Summary: {summary}")
        print(f"   Description: {len(description)} characters")
        print(f"   Acceptance Criteria: {'Found' if acceptance_criteria else 'Not found'}")
        
        # Step 2: Generate test cases with AI
        print(f"\n🤖 Step 2: Generating test cases with AI...")
        print(f"   Using: {llm.model}")
        print(f"   This may take 20-30 seconds...")
        
        # Build the prompt
        sys_prompt = """You are an expert QA test case designer. Your task is to analyze Jira tickets and create comprehensive, detailed test cases.

TESTING PHILOSOPHY:
For EACH requirement identified, create exactly THREE test cases:
1. One POSITIVE test (happy path)
2. One NEGATIVE test (error handling)
3. One EDGE CASE test (boundary conditions)

This ensures complete coverage with clear traceability.

CRITICAL: You MUST follow this two-phase structured approach:

PHASE 1 - REQUIREMENT EXTRACTION:
First, identify and extract ALL distinct requirements from the ticket:

CRITICAL GRANULARITY RULES:
- DO NOT consolidate multiple behaviors into one requirement
- Each testable behavior = 1 separate requirement
- If you find fewer than 8 requirements, you're consolidating too much
- Count mentions in the ticket and create requirements accordingly

SPECIFIC EXTRACTION RULES:
1. FORM FIELDS: If the ticket mentions fields, create 1 requirement PER FIELD
   Example: "Form has First name, Last name, Email" = 3 separate requirements
   - REQ-001: First name field exists and accepts input
   - REQ-002: Last name field exists and accepts input  
   - REQ-003: Email field exists and accepts valid email format

2. VALIDATION RULES: Create 1 requirement PER VALIDATION
   Example: "Email is required and must be valid format" = 2 requirements
   - REQ-004: Email field is required (cannot be empty)
   - REQ-005: Email field validates email format

3. BUTTONS/ACTIONS: Create 1 requirement PER BUTTON BEHAVIOR
   Example: "Send button activates when form valid" = 1 requirement
   Example: "Cancel button closes form" = 1 requirement

4. UI ELEMENTS: Create 1 requirement PER ELEMENT
   - Heading text = 1 requirement
   - Introduction text = 1 requirement
   - Tooltip = 1 requirement
   - Each dropdown option = 1 requirement

5. BEHAVIORS: Create 1 requirement PER DISTINCT BEHAVIOR
   - Data retention = 1 requirement
   - Data loss on refresh = 1 requirement
   - Session management = 1 requirement

EXTRACTION PROCESS:
Step 1: Read the ticket and LIST every element mentioned
Step 2: For each element, create a SEPARATE requirement
Step 3: Look for validation rules and create SEPARATE requirements for each
Step 4: Identify all behaviors and create SEPARATE requirements for each
Step 5: Count your requirements - if less than 10 for a form, you missed some

EXAMPLES FROM A FORM TICKET:
If ticket says: "Create form with First name, Last name, Email, Phone. Email is required. Phone is optional."

You MUST create AT LEAST these requirements:
- REQ-001: First name field exists and accepts text input
- REQ-002: Last name field exists and accepts text input
- REQ-003: Email field exists and accepts text input
- REQ-004: Email field is required (validation)
- REQ-005: Email field validates email format (validation)
- REQ-006: Phone field exists and accepts numeric input
- REQ-007: Phone field is optional (can be left empty)
- REQ-008: Form has Submit button
- REQ-009: Submit button is enabled when required fields filled
- REQ-010: Submit button submits data when clicked

That's 10 requirements from a simple form description!

MANDATORY MINIMUM:
- Simple feature: Minimum 8 requirements
- Form with 5+ fields: Minimum 12 requirements
- Complex workflow: Minimum 15 requirements

If you find fewer requirements, you are CONSOLIDATING and must break them down further.

Extract from:
- Acceptance Criteria (highest priority)
- Description (look for EVERY field, button, validation, behavior)
- UI elements mentioned
- Business logic rules
- Error handling
- Data persistence rules

PHASE 2 - TEST CASE GENERATION:
After identifying ALL requirements, create test cases using the 1:3 FORMULA:

CRITICAL FORMULA:
For N requirements identified → Generate exactly N × 3 test cases
Example: 10 requirements → 30 test cases (10 Positive + 10 Negative + 10 Edge Cases)
Example: 15 requirements → 45 test cases (15 Positive + 15 Negative + 15 Edge Cases)

FOR EACH REQUIREMENT, CREATE THESE THREE TEST CASES:

1. **POSITIVE TEST** (Happy Path):
   - Test the requirement with valid inputs and expected behavior
   - Verify successful workflow
   - Priority: Usually 1 (Critical) or 2 (High)
   - test_type: 'Positive'
   - Steps: 3-8 steps covering complete user journey

2. **NEGATIVE TEST** (Error Handling):
   - Test the requirement with invalid inputs
   - Verify proper error handling and messages
   - Priority: Usually 1 or 2 for critical validations
   - test_type: 'Negative'
   - Steps: 3-8 steps showing error conditions

3. **EDGE CASE TEST** (Boundary Conditions):
   - Test the requirement at boundaries and limits
   - Verify behavior with special characters, empty values, max length, etc.
   - Priority: Usually 2 or 3 (Medium/Low)
   - test_type: 'Edge Case'
   - Steps: 3-8 steps testing boundaries

TEST CASE NAMING:
Use format: '[REQ-ID] [Type]: [Description]'
Examples:
- 'REQ-001 Positive: Valid email format accepted'
- 'REQ-005 Negative: Missing first name shows error'
- 'REQ-003 Edge Case: Username with maximum 50 characters'

STEP COMPLETENESS:
Each step MUST have:
- action: Clear, specific action to perform
- expected: Observable, verifiable expected result

REQUIRED JSON OUTPUT:
{
  "requirements": [
    {"id": "REQ-001", "description": "Clear requirement", "source": "Acceptance Criteria"}
  ],
  "test_cases": [
    {
      "requirement_id": "REQ-001",
      "requirement_desc": "Brief summary",
      "title": "REQ-001 Positive: Title",
      "priority": 1,
      "test_type": "Positive",
      "tags": ["tag1", "tag2"],
      "steps": [
        {"action": "Specific action", "expected": "Expected result"}
      ]
    }
  ]
}

MANDATORY RULES:
1. Identify ALL requirements first (PHASE 1) - be exhaustive
2. For EACH requirement, create EXACTLY 3 test cases
3. Formula: N requirements → N × 3 test cases
4. Minimum 10 requirements for any substantial feature
5. Break down requirements into atomic, testable pieces
6. Each test case must have 3-8 detailed steps"""


        user_prompt = f"""Analyze this Jira ticket and generate comprehensive test cases:

TICKET: {ticket_key}
SUMMARY: {summary}

DESCRIPTION:
{description}

ACCEPTANCE CRITERIA:
{acceptance_criteria if acceptance_criteria else "No explicit acceptance criteria provided - extract requirements from description"}

Generate test cases following the 3-per-requirement rule (Positive, Negative, Edge Case)."""

        # Call AI
        response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=16000)
        
        if error:
            print(f"\n❌ AI Error: {error}")
            return
        
        # Parse response
        from ai_tester.utils.utils import safe_json_extract
        result = safe_json_extract(response_text)
        
        if not result:
            print(f"\n❌ Failed to parse AI response")
            print(f"Raw response (first 500 chars):")
            print(response_text[:500])
            return
        
        print(f"   ✅ AI generation complete!")

        # Critic Review
        print(f"\n👨‍⚖️  Critic Review: Validating quality...")
        critic_data, critic_err = critic_review(llm, summary, requirements, test_cases)
        
        if critic_data:
            approved = critic_data.get("approved", False)
            quality = critic_data.get("overall_quality", "unknown")
            
            print(f"   Quality: {quality.upper()}")
            print(f"   Status: {'✅ APPROVED' if approved else '⚠️  HAS ISSUES'}")
            
            if not approved:
                print(f"\n   Issues found:")
                for issue in critic_data.get('issues_found', [])[:3]:
                    print(f"      • {issue.get('description')}")
                print(f"\n   💡 Consider regenerating or manually reviewing these test cases")
        
        # Step 3: Display results
        requirements = result.get("requirements", [])
        test_cases = result.get("test_cases", [])
        
        print(f"\n" + "=" * 80)
        print(f"📊 GENERATION RESULTS")
        print("=" * 80)
        print(f"\n✅ Generated:")
        print(f"   - {len(requirements)} requirement(s)")
        print(f"   - {len(test_cases)} test case(s)")
        
        # Display requirements
        print(f"\n" + "=" * 80)
        print(f"📋 REQUIREMENTS IDENTIFIED:")
        print("=" * 80)
        
        for i, req in enumerate(requirements, 1):
            req_id = req.get("id", f"REQ-{i:03d}")
            req_desc = req.get("description", "")
            req_source = req.get("source", "Unknown")
            
            print(f"\n{req_id} [{req_source}]")
            print(f"  {req_desc}")
        
        # Display test cases
        print(f"\n" + "=" * 80)
        print(f"🧪 TEST CASES GENERATED:")
        print("=" * 80)
        
        for i, tc in enumerate(test_cases, 1):
            title = tc.get("title", f"Test Case {i}")
            priority = tc.get("priority", 2)
            test_type = tc.get("test_type", "Positive")
            req_id = tc.get("requirement_id", "")
            tags = tc.get("tags", [])
            steps = tc.get("steps", [])
            
            priority_labels = {1: "🔴 CRITICAL", 2: "🟡 HIGH", 3: "🟢 MEDIUM", 4: "⚪ LOW"}
            priority_label = priority_labels.get(priority, "MEDIUM")
            
            print(f"\n{'─' * 80}")
            print(f"TEST CASE #{i}: {title}")
            print(f"{'─' * 80}")
            print(f"Requirement: {req_id}")
            print(f"Type:        {test_type}")
            print(f"Priority:    {priority_label}")
            if tags:
                print(f"Tags:        {', '.join(tags)}")
            
            print(f"\nSteps ({len(steps)}):")
            for j, step in enumerate(steps, 1):
                action = step.get("action", "")
                expected = step.get("expected", "")
                print(f"\n  Step {j}:")
                print(f"    Action:   {action}")
                print(f"    Expected: {expected}")
        
        # Step 4: Save to file
        print(f"\n" + "=" * 80)
        print(f"💾 SAVING RESULTS...")
        print("=" * 80)
        
        output_file = f"test_cases_{ticket_key.replace('-', '_')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Saved to: {output_file}")
        
        # Summary
        print(f"\n" + "=" * 80)
        print(f"✅ GENERATION COMPLETE!")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  - Ticket:        {ticket_key}")
        print(f"  - Requirements:  {len(requirements)}")
        print(f"  - Test Cases:    {len(test_cases)}")
        print(f"  - Total Steps:   {sum(len(tc.get('steps', [])) for tc in test_cases)}")
        print(f"  - Saved to:      {output_file}")
        
        # Quality check
        expected_count = len(requirements) * 3
        if len(test_cases) == expected_count:
            print(f"\n✅ Quality Check: PASSED (3 test cases per requirement)")
        else:
            print(f"\n⚠️  Quality Check: Expected {expected_count} test cases, got {len(test_cases)}")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("🤖 AI TEST CASE GENERATOR")
    print("=" * 80)
    
    # Check credentials
    if not all([os.getenv("JIRA_BASE_URL"), os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")]):
        print("\n❌ Error: Jira credentials not found in .env file!")
        return
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ Error: OpenAI API key not found in .env file!")
        return
    
    print("\n✅ Credentials loaded")
    print(f"   Jira:   {os.getenv('JIRA_BASE_URL')}")
    print(f"   OpenAI: {os.getenv('OPENAI_MODEL', 'gpt-4o-2024-08-06')}")
    
    # Get ticket key
    print("\n" + "-" * 80)
    print("\nEnter the Jira ticket key to generate test cases for:")
    print("(e.g., UEX-123, PROJ-456, STORY-789)")
    print("\nOr press Enter to use a test key: UEX-124")
    
    ticket_key = input("\nTicket Key: ").strip().upper()
    
    if not ticket_key:
        ticket_key = "UEX-124"
        print(f"Using default: {ticket_key}")
    
    # Generate test cases
    generate_test_cases(ticket_key)
    
    # Ask if they want to generate more
    print("\n" + "-" * 80)
    another = input("\nGenerate test cases for another ticket? (y/n): ").strip().lower()
    if another == 'y':
        main()
    else:
        print("\n👋 Done!")
        print("\nNext steps:")
        print("  1. Review the generated JSON file")
        print("  2. Import test cases into your test management system")
        print("  3. Or run the full GUI (Option 3) for more features!")


if __name__ == "__main__":
    main()