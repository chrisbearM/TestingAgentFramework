"""
Test Case Generation Utilities
Helper functions for AI-powered test case generation with critic review and fixing
"""

import json
import sys
from typing import Dict, List, Any, Tuple, Optional


def safe_print(message: str):
    """Print message with UTF-8 encoding, handling Windows console encoding issues"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback: encode to ascii with replacement for unsupported characters
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)


def critic_review(llm, summary, requirements, test_cases_data):
    """Review test cases for quality and reject nonsensical ones."""

    sys_prompt = """You are a Senior QA Manager reviewing test cases.

CRITICAL: Reject test cases that are:
- Nonsensical or don't make logical sense
- Too simplistic (only 1-2 steps when more are needed for proper testing)
- Don't actually test the requirement
- Repetitive or redundant
- Unrealistic or impossible to execute

Check:
1. Does test case count = requirements × 3?
2. Are tests realistic and executable?
3. Do tests actually test what they claim to test?
4. Are steps detailed enough? Tests can have 3+ steps - some simple tests may only need 3 steps, complex tests may need 8+ steps. Judge based on what the test logically requires.
5. Do steps follow the legacy format (alternating "Step N:" and "Expected Result:" strings)?
6. **CRITICAL**: Does EVERY "Step N:" have an immediately following "Expected Result:" line? This is MANDATORY - no exceptions!

IMPORTANT: Be flexible with step counts. A test case can have:
- 3 steps if it's testing something simple
- 4-6 steps for typical scenarios
- 7+ steps for complex scenarios that logically require more detail

Only flag step count as an issue if the test is genuinely too simplistic (1-2 steps) or if a complex scenario is under-specified.

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
            steps = tc.get('steps', [])
            # Count actual steps (alternating format: Step, Expected Result, Step, Expected Result)
            step_count = len([s for s in steps if s.startswith('Step ')])
            user_prompt += f"  • [{tc.get('test_type')}] {tc.get('title')} ({step_count} steps)\n"

    user_prompt += f"\nExpected: {len(requirements)} × 3 = {len(requirements) * 3} tests\nActual: {len(test_cases_data)} tests"

    # Use gpt-4o-mini for critic review (cost optimization)
    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=1500, model="gpt-4o-mini-2024-07-18")

    if error:
        return (None, error)

    from ai_tester.utils.utils import safe_json_extract
    return (safe_json_extract(response_text), None)

def fixer(llm, requirements, test_cases_data, critic_feedback):
    """Fix test cases based on critic feedback instead of regenerating from scratch."""

    sys_prompt = """You are an expert QA Test Case Fixer. Your job is to take existing test cases that have issues and FIX them based on specific feedback.

YOUR ROLE:
- You receive test cases that were rejected by the critic
- You receive specific feedback about what's wrong with each test case
- You must FIX the problematic test cases, keeping the good ones unchanged
- You should ADD missing test cases if the count is wrong
- You should REMOVE duplicate or redundant test cases
- You should IMPROVE test cases that are too simplistic or don't make sense

CRITICAL RULES:
1. Maintain the 3-per-requirement rule (Positive, Negative, Edge Case)
2. Each test case must have 3+ detailed steps (simple tests need 3 steps, complex scenarios may need 8+ steps)
3. **MANDATORY**: EVERY "Step N:" line MUST be immediately followed by an "Expected Result:" line - no exceptions!
4. Steps must be realistic and executable
5. Test cases must actually test what they claim to test
6. Keep the same requirement_id structure
7. Preserve test_type (Positive/Negative/Edge Case) when fixing

FIXING STRATEGIES:
- If a test is too simplistic: Add more detailed steps
- If a test doesn't make sense: Rewrite it to be logical and coherent
- If a test is redundant: Remove it or make it unique
- **If ANY step is missing its "Expected Result:" line: Add it immediately after that step - THIS IS CRITICAL!**
- If test doesn't match requirement: Align it properly
- If count is wrong: Add missing tests or remove duplicates

Return JSON in the SAME format as input:
{
  "requirements": [...],
  "test_cases": [
    {
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
  ]
}"""

    issues = critic_feedback.get('issues_found', [])
    recommendation = critic_feedback.get('recommendation', '')

    user_prompt = f"""Fix these test cases based on the critic's feedback:

REQUIREMENTS ({len(requirements)}):
{json.dumps(requirements, indent=2)}

CURRENT TEST CASES ({len(test_cases_data)}):
{json.dumps(test_cases_data, indent=2)}

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
    user_prompt += f"\n\nFix the test cases to address ALL issues above. Return the complete fixed test cases in JSON format."

    # Use gpt-4o-mini for fixer (cost optimization) - reduced tokens by 25%
    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=12000, model="gpt-4o-mini-2024-07-18")

    if error:
        return (None, error)

    from ai_tester.utils.utils import safe_json_extract
    return (safe_json_extract(response_text), None)

def generate_test_cases_with_retry(llm, sys_prompt, user_prompt, summary, requirements_for_review, max_retries=2, progress_callback=None):
    """Generate test cases with critic review and fixer mechanism."""

    result = None

    for attempt in range(max_retries + 1):
        is_retry = attempt > 0

        if is_retry:
            safe_print(f"\n🔄 Fix attempt {attempt}/{max_retries}...")
            safe_print("   Using fixer to address critic feedback...")
            if progress_callback:
                progress_callback("fixer", f"Fixing test cases (attempt {attempt}/{max_retries})...")

        # Generate or use existing result
        if not is_retry or result is None:
            # Initial generation
            if progress_callback:
                progress_callback("generation", "Generating test cases with AI...")

            # Reduced max_tokens by 25% for cost optimization (16000 -> 12000)
            response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=12000)

            if error:
                safe_print(f"\n❌ AI Error: {error}")
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

        test_cases = result.get("test_cases", [])
        requirements = result.get("requirements", [])

        # Run critic review
        safe_print(f"\n👨‍⚖️  Critic Review (Attempt {attempt + 1})...")
        if progress_callback:
            progress_callback("critic_review", f"Critic reviewing test cases (attempt {attempt + 1})...")

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

        if not approved and attempt < max_retries:
            safe_print(f"\n   ❌ Test cases have issues. Issues found:")
            for i, issue in enumerate(issues[:10], 1):  # Show up to 10 issues
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
            if progress_callback:
                progress_callback("fixer", "Fixing test cases based on critic feedback...")

            fixed_result, fixer_err = fixer(llm, requirements, test_cases, critic_data)

            if fixer_err:
                safe_print(f"   ⚠️  Fixer failed: {fixer_err}")
                if attempt < max_retries:
                    continue
                return result, critic_data

            if not fixed_result:
                safe_print(f"   ⚠️  Fixer returned no result")
                if attempt < max_retries:
                    continue
                return result, critic_data

            # Update result with fixed test cases
            result = fixed_result
            safe_print(f"   ✅ Fixer completed - test cases updated")

            # Continue to next iteration to re-review fixed test cases
            continue

        # Approved or max retries reached
        if not approved:
            safe_print(f"\n   ⚠️  Max retries reached. Proceeding with current results despite issues.")
            safe_print(f"   Issues summary:")
            for i, issue in enumerate(issues[:5], 1):
                safe_print(f"      {i}. {issue.get('test_case_title', 'Unknown')}: {issue.get('description', '')}")

        return result, critic_data

    return None, None
