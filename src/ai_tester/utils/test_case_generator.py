"""
Test Case Generation Utilities
Helper functions for AI-powered test case generation with critic review and fixing
"""

import json
from typing import Dict, List, Any, Tuple, Optional


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
2. Each test case must have 3-8 detailed steps
3. Steps must be realistic and executable
4. Test cases must actually test what they claim to test
5. Keep the same requirement_id structure
6. Preserve test_type (Positive/Negative/Edge Case) when fixing

FIXING STRATEGIES:
- If a test is too simplistic: Add more detailed steps
- If a test doesn't make sense: Rewrite it to be logical and coherent
- If a test is redundant: Remove it or make it unique
- If steps are missing expected results: Add clear expected outcomes
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
        {"action": "Specific action", "expected": "Expected result"}
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

    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=16000)

    if error:
        return (None, error)

    from ai_tester.utils.utils import safe_json_extract
    return (safe_json_extract(response_text), None)

def generate_test_cases_with_retry(llm, sys_prompt, user_prompt, summary, requirements_for_review, max_retries=2):
    """Generate test cases with critic review and fixer mechanism."""

    result = None

    for attempt in range(max_retries + 1):
        is_retry = attempt > 0

        if is_retry:
            print(f"\n🔄 Fix attempt {attempt}/{max_retries}...")
            print("   Using fixer to address critic feedback...")

        # Generate or use existing result
        if not is_retry or result is None:
            # Initial generation
            response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=16000)

            if error:
                print(f"\n❌ AI Error: {error}")
                if attempt < max_retries:
                    continue
                return None, None

            # Parse response
            from ai_tester.utils.utils import safe_json_extract
            result = safe_json_extract(response_text)

            if not result:
                print(f"\n❌ Failed to parse AI response")
                if attempt < max_retries:
                    continue
                return None, None

        test_cases = result.get("test_cases", [])
        requirements = result.get("requirements", [])

        # Run critic review
        print(f"\n👨‍⚖️  Critic Review (Attempt {attempt + 1})...")
        critic_data, critic_err = critic_review(llm, summary, requirements_for_review or requirements, test_cases)

        if not critic_data:
            print(f"   ⚠️  Critic review failed: {critic_err}")
            # If critic fails, still return results on last attempt
            if attempt == max_retries:
                return result, None
            continue

        approved = critic_data.get("approved", False)
        quality = critic_data.get("overall_quality", "unknown")
        confidence = critic_data.get("confidence_score", 0)
        issues = critic_data.get('issues_found', [])

        print(f"   Quality:     {quality.upper()}")
        print(f"   Confidence:  {confidence}%")
        print(f"   Status:      {'✅ APPROVED' if approved else '⚠️  HAS ISSUES'}")

        if not approved and attempt < max_retries:
            print(f"\n   ❌ Test cases have issues. Issues found:")
            for i, issue in enumerate(issues[:10], 1):  # Show up to 10 issues
                tc_title = issue.get('test_case_title', 'Unknown')
                desc = issue.get('description', 'No description')
                suggestion = issue.get('suggestion', '')
                print(f"      {i}. {tc_title}")
                print(f"         Problem: {desc}")
                if suggestion:
                    print(f"         Fix: {suggestion}")

            recommendation = critic_data.get('recommendation', '')
            if recommendation:
                print(f"\n   💡 Recommendation: {recommendation}")

            # Use fixer to fix the test cases instead of regenerating
            print(f"\n   🔧 Calling fixer to address issues...")
            fixed_result, fixer_err = fixer(llm, requirements, test_cases, critic_data)

            if fixer_err:
                print(f"   ⚠️  Fixer failed: {fixer_err}")
                if attempt < max_retries:
                    continue
                return result, critic_data

            if not fixed_result:
                print(f"   ⚠️  Fixer returned no result")
                if attempt < max_retries:
                    continue
                return result, critic_data

            # Update result with fixed test cases
            result = fixed_result
            print(f"   ✅ Fixer completed - test cases updated")

            # Continue to next iteration to re-review fixed test cases
            continue

        # Approved or max retries reached
        if not approved:
            print(f"\n   ⚠️  Max retries reached. Proceeding with current results despite issues.")
            print(f"   Issues summary:")
            for i, issue in enumerate(issues[:5], 1):
                print(f"      {i}. {issue.get('test_case_title', 'Unknown')}: {issue.get('description', '')}")

        return result, critic_data

    return None, None
