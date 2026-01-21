"""
Test Case Generation Utilities
Helper functions for AI-powered test case generation with critic review and fixing
"""

import json
import sys
from typing import Dict, List, Any, Tuple, Optional, Callable

# Model token limits (approximate)
MODEL_TOKEN_LIMITS = {
    "gpt-4o-mini-2024-07-18": 128000,
    "gpt-4o": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
}


def safe_print(message: str):
    """Print message with UTF-8 encoding, handling Windows console encoding issues"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback: encode to ascii with replacement for unsupported characters
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)


def safe_progress_callback(callback: Optional[Callable], substep: str, message: str):
    """Safely call progress callback with error handling"""
    if callback:
        try:
            callback(substep, message)
        except Exception as e:
            safe_print(f"Warning: Progress callback failed: {e}")


def validate_token_limit(sys_prompt: str, user_prompt: str, max_tokens: int, model: str = None) -> Tuple[bool, Optional[str]]:
    """Validate that prompt + completion won't exceed token limits (approximate)"""
    # Get model limit
    limit = MODEL_TOKEN_LIMITS.get(model, 8192) if model else 128000

    # Approximate token count: ~4 characters per token for English text
    # This is a rough estimate but catches obviously oversized prompts
    estimated_prompt_tokens = (len(sys_prompt) + len(user_prompt)) // 4
    total_needed = estimated_prompt_tokens + max_tokens

    if total_needed > limit:
        return False, f"Prompt requires approximately {total_needed} tokens but model limit is {limit}. Consider reducing prompt size."

    # Warn if approaching limit (80% threshold)
    if total_needed > limit * 0.8:
        safe_print(f"   ⚠️ Warning: Prompt size is {int((total_needed/limit)*100)}% of token limit")

    return True, None


def critic_review(llm, summary, requirements, test_cases_data):
    """Review test cases for quality and reject nonsensical ones."""

    sys_prompt = """You are a Senior QA Manager evaluating test cases for production readiness.

YOUR GOAL: APPROVE test cases if they meet quality standards. REJECT if they need significant improvements.

APPROVE test cases if they meet these quality standards:
- Make logical sense and test the stated requirements
- Have adequate detail (MOST tests have 3+ steps with clear actions)
- Follow the alternating "Step N:" / "Expected Result:" format correctly
- Cover approximately the right number of scenarios (within 80-120% of requirements × 3)
- Are realistic and executable
- Test cases are sufficiently detailed to be useful for actual testing

VALID TEST STEP FORMATS (accept all of these - prefer SPECIFIC names when available):
1. UI/Black-box steps:
   - "Step N: Click the Submit button"
   - "Expected Result: Form is submitted successfully"

2. API verification steps (use SPECIFIC endpoint names, fields, status codes from requirements):
   - "Step N: Send POST request to /api/users endpoint"
   - "Expected Result: API returns 201 Created with 'userId', 'email' fields"
   - "Step N: Send GET request to /api/orders/{id} endpoint"
   - "Expected Result: API returns 200 OK with 'status', 'items', 'total' fields"
   - "Step N: Send request with missing 'email' field"
   - "Expected Result: API returns 400 Bad Request with validation error"

3. Database verification steps (use SPECIFIC table names, column names from requirements):
   - "Step N: Query 'users' table for the new record"
   - "Expected Result: Record exists with 'email', 'created_at', 'status'='active'"
   - "Step N: Query 'orders' table for order ID"
   - "Expected Result: Record has 'status'='completed', 'total' matches expected value"
   - "Step N: Query 'audit_log' table for the operation"
   - "Expected Result: Entry exists with 'action'='CREATE', 'entity_id', 'timestamp'"

REJECT if test cases have SIGNIFICANT quality issues:
- More than 20% of test cases lack sufficient detail (only 1-2 vague steps)
- More than 20% of test cases have broken step format (missing Expected Results)
- Missing more than 25% of expected test cases (count < requirements × 2.25)
- More than 20% of test cases are nonsensical, unrealistic, or don't test their stated requirement
- Test cases are too simplistic to be useful (e.g., "Step 1: Test the feature, Expected Result: It works")

For MINOR issues (these should NOT cause rejection):
- A few tests (less than 15%) could be more detailed but are still testable
- Minor formatting inconsistencies in a few tests
- Test count slightly off (within 20% of target)
- Minor redundancy between some tests
- Some tests could have 1 more step but are still adequate

Evaluation approach:
- If overall_quality would be "excellent" or "good": APPROVE (even if there are a few minor issues)
- If overall_quality would be "needs_improvement": REJECT (send to fixer)
- If overall_quality would be "poor": REJECT (send to fixer)

When you find minor issues but still approve:
- Set approved = true
- List them in issues_found as suggestions
- Set overall_quality to "good" instead of "excellent"

When you reject:
- Set approved = false
- List specific issues with clear suggestions for the fixer
- The fixer will address these and you'll review again

Return JSON:
{
  "approved": true/false,
  "overall_quality": "excellent"/"good"/"needs_improvement"/"poor",
  "confidence_score": 0-100,
  "issues_found": [
    {"test_case_title": "...", "description": "What's wrong", "suggestion": "How to fix"}
  ],
  "summary": "Brief review summary",
  "recommendation": "Approve or list specific fixes needed"
}

Focus on actual testability and usefulness. Tests lacking steps or detail are real problems that should be rejected."""

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
            steps = tc.get('steps', [])
            # Count actual steps (alternating format: Step, Expected Result, Step, Expected Result)
            step_count = len([s for s in steps if s.startswith('Step ')])
            user_prompt += f"  • [{tc.get('test_type')}] {tc.get('title')} ({step_count} steps)\n"

    user_prompt += f"\nExpected: {len(requirements)} × 3 = {len(requirements) * 3} tests\nActual: {len(test_cases_data)} tests"

    # Validate token limit before making API call
    model = "gpt-4o-mini-2024-07-18"
    max_tokens = 1500
    valid, validation_error = validate_token_limit(sys_prompt, user_prompt, max_tokens, model)
    if not valid:
        return (None, validation_error)

    # Use gpt-4o-mini for critic review (cost optimization)
    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=max_tokens, model=model)

    if error:
        return (None, error)

    # Validate response is not empty
    if not response_text:
        return (None, "LLM returned empty response")

    from ai_tester.utils.utils import safe_json_extract
    result = safe_json_extract(response_text)

    # Validate result structure
    if not result:
        return (None, "Failed to parse LLM response as JSON")

    if not isinstance(result, dict):
        return (None, "LLM response is not a valid dictionary")

    return (result, None)

def fixer(llm, requirements, test_cases_data, critic_feedback):
    """Fix test cases based on critic feedback instead of regenerating from scratch."""

    sys_prompt = """You are an expert QA Test Case Fixer. Your job is to take existing test cases that have issues and FIX them based on specific feedback.

YOUR ROLE:
- You receive test cases that were rejected by the critic
- You receive specific feedback about what's wrong with each test case
- You must FIX ONLY the problematic test cases (don't regenerate good ones)
- You should ADD new test cases if the count is wrong
- You should identify test cases to REMOVE if they're redundant

CRITICAL RULES:
1. Maintain the 3-per-requirement rule (Positive, Negative, Edge Case)
2. Each test case must have 3+ detailed steps (simple tests need 3 steps, complex scenarios may need 8+ steps)
3. **MANDATORY**: EVERY "Step N:" line MUST be immediately followed by an "Expected Result:" line - no exceptions!
4. Steps must be realistic and executable
5. Test cases must actually test what they claim to test
6. Keep the same requirement_id structure
7. Preserve test_type (Positive/Negative/Edge Case) when fixing

VALID TEST STEP PATTERNS (use SPECIFIC names from requirements):
1. UI/Black-box steps:
   - "Step N: Click the Submit button"
   - "Expected Result: Form is submitted successfully"

2. API verification steps (use SPECIFIC endpoint names, fields, status codes):
   - "Step N: Send POST request to /api/users endpoint"
   - "Expected Result: API returns 201 Created with 'userId', 'email' fields"
   - "Step N: Send GET request to /api/orders/{id}"
   - "Expected Result: API returns 200 OK with 'status', 'items', 'total'"
   - "Step N: Send request with invalid 'email' format"
   - "Expected Result: API returns 400 Bad Request with field validation error"

3. Database verification steps (use SPECIFIC table names, column names):
   - "Step N: Query 'users' table for the created record"
   - "Expected Result: Record exists with 'email', 'created_at', 'status'='active'"
   - "Step N: Query 'orders' table to verify update"
   - "Expected Result: Record 'status' field updated to 'completed'"
   - "Step N: Query 'audit_log' table for operation entry"
   - "Expected Result: Entry with 'action'='UPDATE', 'entity_id', 'user_id'"

FIXING STRATEGIES:
- If a test is too simplistic: Add more detailed steps
- If a test doesn't make sense: Rewrite it to be logical and coherent
- If a test is redundant: Mark it for removal or make it unique
- **If ANY step is missing its "Expected Result:" line: Add it immediately after that step - THIS IS CRITICAL!**
- If test doesn't match requirement: Align it properly
- If count is wrong: Add missing tests
- If requirements mention APIs but no API steps exist: Add API verification steps WITH SPECIFIC endpoint names
- If requirements mention data persistence but no DB steps exist: Add database verification steps WITH SPECIFIC table/field names
- If API/DB steps are too generic: Replace with SPECIFIC names from requirements

IMPORTANT - EFFICIENT OUTPUT:
Only return test cases that you ACTUALLY CHANGED or ADDED. Don't return unchanged test cases!

Return JSON in this format:
{
  "requirements": [...],
  "fixed_test_cases": [
    {
      "original_title": "REQ-001 Positive: Original Title",
      "test_case": {
        "requirement_id": "REQ-001",
        "requirement_desc": "Brief summary",
        "title": "REQ-001 Positive: Title",
        "priority": 1,
        "test_type": "Positive",
        "tags": ["tag1", "tag2"],
        "steps": [
          "Step 1: Specific action",
          "Expected Result: Expected outcome",
          "Step 2: Next action",
          "Expected Result: Next expected outcome"
        ]
      }
    }
  ],
  "new_test_cases": [
    {
      "requirement_id": "REQ-001",
      ...
    }
  ],
  "remove_titles": ["REQ-001 Negative: Redundant test"]
}"""

    issues = critic_feedback.get('issues_found', [])
    recommendation = critic_feedback.get('recommendation', '')

    user_prompt = f"""Fix these test cases based on the critic's feedback:

REQUIREMENTS ({len(requirements)}):
{json.dumps(requirements)}

CURRENT TEST CASES ({len(test_cases_data)}):
{json.dumps(test_cases_data)}

CRITIC FEEDBACK:
Overall Quality: {critic_feedback.get('overall_quality', 'unknown')}
Confidence Score: {critic_feedback.get('confidence_score', 0)}%

SPECIFIC ISSUES TO FIX:
"""

    for i, issue in enumerate(issues, 1):
        tc_title = issue.get('test_case_title', 'Unknown')
        description = issue.get('description', 'No description')
        suggestion = issue.get('suggestion', '')

        user_prompt += f"\n{i}. Test Case: {tc_title}"
        user_prompt += f"\n   Problem: {description}"
        if suggestion:
            user_prompt += f"\n   How to Fix: {suggestion}"
        user_prompt += "\n"

    user_prompt += f"\nOVERALL RECOMMENDATION:\n{recommendation}\n"
    user_prompt += f"\nExpected test count: {len(requirements)} × 3 = {len(requirements) * 3}"
    user_prompt += f"\nCurrent test count: {len(test_cases_data)}"
    user_prompt += f"\n\nIMPORTANT: Only return the test cases you actually FIXED or ADDED. Don't return unchanged test cases - we'll keep those as-is!"

    # Validate token limit before making API call
    model = "gpt-4o-mini-2024-07-18"
    max_tokens = 8000
    valid, validation_error = validate_token_limit(sys_prompt, user_prompt, max_tokens, model)
    if not valid:
        return (None, validation_error)

    # Use gpt-4o-mini for fixer (cost optimization) - reduced tokens significantly by only returning changed test cases
    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=max_tokens, model=model)

    if error:
        return (None, error)

    # Validate response is not empty
    if not response_text:
        return (None, "LLM returned empty response")

    from ai_tester.utils.utils import safe_json_extract
    fixer_result = safe_json_extract(response_text)

    if not fixer_result:
        return (None, "Failed to parse fixer response")

    if not isinstance(fixer_result, dict):
        return (None, "Fixer response is not a valid dictionary")

    # Merge the fixed test cases back into the original array
    fixed_test_cases = fixer_result.get('fixed_test_cases', [])
    new_test_cases = fixer_result.get('new_test_cases', [])
    remove_titles = fixer_result.get('remove_titles', [])
    requirements_updated = fixer_result.get('requirements', requirements)

    # Start with original test cases
    merged_test_cases = test_cases_data.copy()

    # Remove test cases marked for deletion
    if remove_titles:
        merged_test_cases = [tc for tc in merged_test_cases if tc.get('title') not in remove_titles]

    # Apply fixes by replacing test cases with matching titles
    for fix in fixed_test_cases:
        original_title = fix.get('original_title')
        fixed_tc = fix.get('test_case')

        if not original_title or not fixed_tc:
            continue

        # Find and replace the test case
        for i, tc in enumerate(merged_test_cases):
            if tc.get('title') == original_title:
                merged_test_cases[i] = fixed_tc
                break

    # Add new test cases
    if new_test_cases:
        merged_test_cases.extend(new_test_cases)

    # Return in the original format expected by the caller
    return ({
        'requirements': requirements_updated,
        'test_cases': merged_test_cases
    }, None)

def generate_test_cases_with_retry(llm, sys_prompt, user_prompt, summary, requirements_for_review, max_retries=2, progress_callback=None):
    """Generate test cases with critic review and fixer mechanism."""

    result = None

    for attempt in range(max_retries + 1):
        is_retry = attempt > 0

        if is_retry:
            safe_print(f"\n🔄 Fix attempt {attempt}/{max_retries}...")
            safe_print("   Using fixer to address critic feedback...")
            safe_progress_callback(progress_callback, "fixer", f"🔧 Fix Attempt {attempt}/{max_retries}: Addressing critic feedback...")

        # Generate or use existing result
        if not is_retry or result is None:
            # Initial generation
            safe_progress_callback(progress_callback, "generation", "🤖 AI is analyzing requirements and generating test cases...")

            # Validate token limit before making API call
            max_tokens = 12000
            valid, validation_error = validate_token_limit(sys_prompt, user_prompt, max_tokens)
            if not valid:
                safe_print(f"\n❌ Token Limit Error: {validation_error}")
                return None, None

            # Reduced max_tokens by 25% for cost optimization (16000 -> 12000)
            response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=max_tokens)

            if error:
                safe_print(f"\n❌ AI Error: {error}")
                if attempt < max_retries:
                    continue
                return None, None

            # Validate response is not empty
            if not response_text:
                safe_print(f"\n❌ LLM returned empty response")
                if attempt < max_retries:
                    continue
                return None, None

            # Parse response
            from ai_tester.utils.utils import safe_json_extract
            result = safe_json_extract(response_text)

            if not result:
                safe_print(f"\n❌ Failed to parse AI response")
                if attempt < max_retries:
                    continue
                return None, None

            # Validate result structure
            if not isinstance(result, dict):
                safe_print(f"\n❌ AI response is not a valid dictionary")
                if attempt < max_retries:
                    continue
                return None, None

        test_cases = result.get("test_cases", [])
        requirements = result.get("requirements", [])

        # Validate test_cases is a list
        if not isinstance(test_cases, list):
            safe_print(f"\n❌ test_cases is not a list")
            if attempt < max_retries:
                continue
            return None, None

        # Validate requirements is a list
        if not isinstance(requirements, list):
            safe_print(f"\n❌ requirements is not a list")
            if attempt < max_retries:
                continue
            return None, None

        # Send detailed generation results with actual content
        if not is_retry:
            # Show first 5 test cases with their steps
            test_case_preview = []
            for i, tc in enumerate(test_cases[:5], 1):
                tc_title = tc.get('title', 'Untitled')
                tc_type = tc.get('test_type', 'Unknown')
                steps = tc.get('steps', [])
                step_count = len([s for s in steps if s.startswith('Step ')])

                # Show the test case with first 2 steps
                tc_preview = f"\n{i}. [{tc_type}] {tc_title}"
                tc_preview += f"\n   Steps ({step_count} total):"
                for j, step in enumerate(steps[:4], 1):  # Show first 4 lines (2 steps + 2 expected results)
                    tc_preview += f"\n   • {step[:80]}" + ("..." if len(step) > 80 else "")
                if len(steps) > 4:
                    tc_preview += f"\n   • ... and {len(steps) - 4} more lines"
                test_case_preview.append(tc_preview)

            preview_text = "\n".join(test_case_preview)
            more_text = f"\n\n... and {len(test_cases) - 5} more test cases" if len(test_cases) > 5 else ""

            safe_progress_callback(progress_callback, "generation", f"✅ Generated {len(requirements)} requirements and {len(test_cases)} test cases:\n{preview_text}{more_text}")

        # Run critic review
        safe_print(f"\n👨‍⚖️  Critic Review (Attempt {attempt + 1})...")
        safe_progress_callback(progress_callback, "critic_review", f"👨‍⚖️ Critic is reviewing {len(test_cases)} test cases for quality...")

        critic_data, critic_err = critic_review(llm, summary, requirements_for_review or requirements, test_cases)

        if not critic_data:
            safe_print(f"   ⚠️  Critic review failed: {critic_err}")
            # If critic fails, still return results on last attempt
            if attempt == max_retries:
                return result, None
            continue

        approved = critic_data.get("approved", False)
        quality = critic_data.get("overall_quality", "unknown")
        confidence = critic_data.get("confidence_score", 0)
        issues = critic_data.get('issues_found', [])

        safe_print(f"   Quality:     {quality.upper()}")
        safe_print(f"   Confidence:  {confidence}%")
        safe_print(f"   Status:      {'✅ APPROVED' if approved else '⚠️  HAS ISSUES'}")

        # Send detailed critic results with full review
        summary = critic_data.get('summary', 'No summary provided')
        recommendation = critic_data.get('recommendation', '')

        if approved:
            # Show approval with any minor suggestions
            approval_msg = f"✅ CRITIC APPROVED\n\nQuality: {quality.upper()}\nConfidence: {confidence}%\n\nSummary: {summary}"
            if issues:
                approval_msg += f"\n\nMinor suggestions ({len(issues)}):"
                for i, issue in enumerate(issues[:5], 1):
                    tc_title = issue.get('test_case_title', 'Unknown')
                    desc = issue.get('description', 'No description')
                    approval_msg += f"\n{i}. {tc_title}: {desc}"
                if len(issues) > 5:
                    approval_msg += f"\n... and {len(issues) - 5} more suggestions"
            safe_progress_callback(progress_callback, "critic_review", approval_msg)
        else:
            # Show rejection with all issues
            rejection_msg = f"⚠️ CRITIC FOUND ISSUES\n\nQuality: {quality.upper()}\nConfidence: {confidence}%\n\nSummary: {summary}"
            if issues:
                rejection_msg += f"\n\nIssues to fix ({len(issues)}):"
                for i, issue in enumerate(issues[:8], 1):  # Show up to 8 issues
                    tc_title = issue.get('test_case_title', 'Unknown')
                    desc = issue.get('description', 'No description')
                    suggestion = issue.get('suggestion', '')
                    rejection_msg += f"\n\n{i}. {tc_title}\n   Problem: {desc}"
                    if suggestion:
                        rejection_msg += f"\n   Fix: {suggestion}"
                if len(issues) > 8:
                    rejection_msg += f"\n\n... and {len(issues) - 8} more issues"
            if recommendation:
                rejection_msg += f"\n\nRecommendation: {recommendation}"
            safe_progress_callback(progress_callback, "critic_review", rejection_msg)

        if not approved and attempt < max_retries:
            safe_print(f"\n   ❌ Test cases have issues. Issues found:")

            # Print to console
            for i, issue in enumerate(issues[:5], 1):
                tc_title = issue.get('test_case_title', 'Unknown')
                desc = issue.get('description', 'No description')
                suggestion = issue.get('suggestion', '')
                safe_print(f"      {i}. {tc_title}")
                safe_print(f"         Problem: {desc}")
                if suggestion:
                    safe_print(f"         Fix: {suggestion}")

            recommendation = critic_data.get('recommendation', '')
            if recommendation:
                safe_print(f"\n   💡 Recommendation: {recommendation}")

            # Use fixer to fix the test cases instead of regenerating
            safe_print(f"\n   🔧 Calling fixer to address issues...")

            # Build detailed fixer status message with actual issues
            fixer_msg = f"🔧 FIXER WORKING\n\nAddressing {len(issues)} issues:\n"
            for i, issue in enumerate(issues[:8], 1):  # Show up to 8 issues
                tc_title = issue.get('test_case_title', 'Unknown')
                problem = issue.get('description', 'No description')
                suggestion = issue.get('suggestion', '')

                fixer_msg += f"\n{i}. Test Case: {tc_title}"
                fixer_msg += f"\n   Issue: {problem[:150]}" + ("..." if len(problem) > 150 else "")
                if suggestion:
                    fixer_msg += f"\n   Fix: {suggestion[:150]}" + ("..." if len(suggestion) > 150 else "")
                fixer_msg += "\n"

            if len(issues) > 8:
                fixer_msg += f"\n... and {len(issues) - 8} more issues"

            safe_progress_callback(progress_callback, "fixer", fixer_msg)

            original_tc_count = len(test_cases)
            fixed_result, fixer_err = fixer(llm, requirements, test_cases, critic_data)

            if fixer_err:
                safe_print(f"   ⚠️  Fixer failed: {fixer_err}")
                safe_progress_callback(progress_callback, "fixer", f"❌ Fixer encountered an error: {fixer_err}")
                if attempt < max_retries:
                    continue
                return result, critic_data

            if not fixed_result:
                safe_print(f"   ⚠️  Fixer returned no result")
                safe_progress_callback(progress_callback, "fixer", "⚠️ Fixer did not return results")
                if attempt < max_retries:
                    continue
                return result, critic_data

            # Update result with fixed test cases
            result = fixed_result
            safe_print(f"   ✅ Fixer completed - test cases updated")

            fixed_test_cases = fixed_result.get("test_cases", [])

            # Show what changed
            num_fixed = len(fixed_result.get('fixed_test_cases', []))
            num_added = len(fixed_result.get('new_test_cases', []))
            num_removed = len(fixed_result.get('remove_titles', []))

            change_summary = f"✅ FIXER COMPLETED\n\n"
            change_summary += f"Test cases modified: {num_fixed}\n"
            if num_added > 0:
                change_summary += f"Test cases added: {num_added}\n"
            if num_removed > 0:
                change_summary += f"Test cases removed: {num_removed}\n"
            change_summary += f"Test cases unchanged: {original_tc_count - num_fixed - num_removed}\n"
            change_summary += f"Total after fixes: {len(fixed_test_cases)} test cases\n"

            # Show sample of fixed test cases with details
            if num_fixed > 0:
                change_summary += f"\nFixed test cases (showing details):\n"
                for i, fix in enumerate(fixed_result.get('fixed_test_cases', [])[:5], 1):
                    original_title = fix.get('original_title', 'Unknown')
                    fixed_tc = fix.get('test_case', {})
                    tc_title = fixed_tc.get('title', 'Untitled')
                    steps = fixed_tc.get('steps', [])
                    step_count = len([s for s in steps if s.startswith('Step ')])

                    change_summary += f"\n{i}. {tc_title}"
                    change_summary += f"\n   Now has {step_count} steps:"
                    # Show first 2 step lines
                    for step in steps[:2]:
                        change_summary += f"\n   • {step[:80]}" + ("..." if len(step) > 80 else "")
                    if len(steps) > 2:
                        change_summary += f"\n   • ... and {len(steps) - 2} more lines"
                    change_summary += "\n"

                if num_fixed > 5:
                    change_summary += f"\n... and {num_fixed - 5} more fixed test cases"

            # Show sample of new test cases
            if num_added > 0:
                change_summary += f"\nNew test cases added:\n"
                for i, new_tc in enumerate(fixed_result.get('new_test_cases', [])[:3], 1):
                    tc_title = new_tc.get('title', 'Untitled')
                    tc_type = new_tc.get('test_type', 'Unknown')
                    steps = new_tc.get('steps', [])
                    step_count = len([s for s in steps if s.startswith('Step ')])
                    change_summary += f"\n{i}. [{tc_type}] {tc_title} ({step_count} steps)"
                if num_added > 3:
                    change_summary += f"\n... and {num_added - 3} more"

            change_summary += f"\n\nPreparing for re-review by critic..."
            safe_progress_callback(progress_callback, "fixer", change_summary)

            # Continue to next iteration to re-review fixed test cases
            continue

        # Approved or max retries reached
        if not approved:
            safe_print(f"\n   ⚠️  Max retries reached. Proceeding with current results despite issues.")
            safe_print(f"   Issues summary:")
            for i, issue in enumerate(issues[:5], 1):
                safe_print(f"      {i}. {issue.get('test_case_title', 'Unknown')}: {issue.get('description', '')}")
            safe_progress_callback(progress_callback, "complete", f"⚠️ Max retries reached - proceeding with {len(test_cases)} test cases (quality: {quality})")
        else:
            # Successfully approved
            safe_progress_callback(progress_callback, "complete", f"✅ Test case generation complete! {len(test_cases)} high-quality test cases generated (quality: {quality})")

        return result, critic_data

    return None, None
