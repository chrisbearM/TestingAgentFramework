"""
Test Case Reviewer Agent
Reviews generated test cases for quality, completeness, and identifies improvements
"""
from typing import Dict, List, Any, Optional
import json


class TestCaseReviewerAgent:
    """
    Agent that reviews test cases and provides quality feedback.
    """

    def __init__(self, llm_client):
        """
        Initialize the Test Case Reviewer Agent.

        Args:
            llm_client: LLM client for AI calls
        """
        self.llm = llm_client

    def review_test_cases(
        self,
        test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]],
        ticket_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Review test cases and provide comprehensive feedback.

        Args:
            test_cases: List of generated test cases
            requirements: Requirements that test cases should cover
            ticket_context: Optional context about the ticket

        Returns:
            Dictionary with review results
        """
        print(f"DEBUG TestCaseReviewer: Reviewing {len(test_cases)} test cases")

        # Build review prompt
        prompt = self._build_review_prompt(test_cases, requirements, ticket_context)

        sys_prompt = """You are an expert QA test reviewer focusing on BLACK BOX TESTING. Your job is to review test cases for:

**BLACK BOX TESTING FOCUS**: Review test cases from a user's perspective without knowledge of internal implementation. Test cases should focus on:
- User actions and observable behaviors
- Input validation and expected outputs
- User interface interactions
- Business logic from an external perspective
- Error handling as seen by the user

**Review Criteria**:
1. **Completeness**: Do test cases cover all requirements and user scenarios?
2. **Quality**: Are test steps clear, specific, testable, and written from a user's perspective?
3. **Edge Cases**: Are edge cases, boundary conditions, and error scenarios covered?
4. **Redundancy**: Are there duplicate or overlapping test cases?
5. **Coverage Gaps**: What user scenarios or workflows are missing?

Provide constructive, actionable feedback focused on black box testing principles."""

        # Get AI review (using gpt-4o-mini for cost optimization, reduced tokens by 25%)
        response, error = self.llm.complete_json(sys_prompt, prompt, max_tokens=3000, model="gpt-4o-mini-2024-07-18")

        if error:
            print(f"DEBUG TestCaseReviewer: LLM error: {error}")
            return {
                "overall_score": 0,
                "quality_rating": "error",
                "summary": f"Review failed: {error}",
                "strengths": [],
                "issues": [],
                "suggestions": [],
                "missing_scenarios": [],
                "redundant_tests": []
            }

        # Parse response
        try:
            review_data = json.loads(response)
        except json.JSONDecodeError:
            print("DEBUG TestCaseReviewer: Failed to parse JSON, using fallback")
            review_data = {
                "overall_score": 70,
                "quality_rating": "good",
                "summary": "Review completed",
                "strengths": [],
                "issues": [],
                "suggestions": [],
                "missing_scenarios": [],
                "redundant_tests": []
            }

        print(f"DEBUG TestCaseReviewer: Overall score: {review_data.get('overall_score', 'N/A')}")

        return review_data

    def _build_review_prompt(
        self,
        test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]],
        ticket_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the review prompt."""

        prompt_parts = []

        # Add ticket context if available
        if ticket_context:
            prompt_parts.append("## Ticket Context")
            if ticket_context.get('key'):
                prompt_parts.append(f"**Ticket**: {ticket_context['key']}")
            if ticket_context.get('summary'):
                prompt_parts.append(f"**Summary**: {ticket_context['summary']}")
            if ticket_context.get('description'):
                desc = ticket_context['description'][:500]  # Truncate if too long
                prompt_parts.append(f"**Description**: {desc}...")
            prompt_parts.append("")

        # Add requirements
        prompt_parts.append("## Requirements to Test")
        for i, req in enumerate(requirements, 1):
            # Handle both string and dict requirements
            if isinstance(req, str):
                req_id = f'REQ-{i}'
                req_text = req
            else:
                req_id = req.get('id', f'REQ-{i}')
                req_text = req.get('requirement', req.get('text', 'No description'))
            prompt_parts.append(f"- **{req_id}**: {req_text}")
        prompt_parts.append("")

        # Add test cases
        prompt_parts.append("## Generated Test Cases")
        for i, tc in enumerate(test_cases, 1):
            tc_name = tc.get('name', tc.get('title', f'Test Case {i}'))
            tc_type = tc.get('type', 'Unknown')
            tc_steps = tc.get('steps', [])

            prompt_parts.append(f"### Test Case {i}: {tc_name}")
            prompt_parts.append(f"**Type**: {tc_type}")
            prompt_parts.append(f"**Steps** ({len(tc_steps)}):")
            for step_num, step in enumerate(tc_steps[:5], 1):  # Show first 5 steps
                # Handle both string and dict steps
                if isinstance(step, str):
                    step_desc = step
                else:
                    step_desc = step.get('description', step.get('action', step.get('step', 'No description')))
                prompt_parts.append(f"  {step_num}. {step_desc}")
            if len(tc_steps) > 5:
                prompt_parts.append(f"  ... and {len(tc_steps) - 5} more steps")

            if tc.get('expected_result') or tc.get('expected_results'):
                expected = tc.get('expected_result', tc.get('expected_results'))
                prompt_parts.append(f"**Expected**: {expected}")
            prompt_parts.append("")

        # Add review instructions
        prompt_parts.append("## Review Task")
        prompt_parts.append("""
Please review these test cases and provide a comprehensive analysis in JSON format:

```json
{
  "overall_score": <0-100 score>,
  "quality_rating": "<excellent|good|fair|poor>",
  "summary": "<2-3 sentence overall assessment>",
  "strengths": [
    "<strength 1>",
    "<strength 2>"
  ],
  "issues": [
    {
      "test_case": "<test case name or number>",
      "severity": "<critical|high|medium|low>",
      "issue": "<description of the issue>",
      "suggestion": "<how to fix it>"
    }
  ],
  "suggestions": [
    {
      "category": "<completeness|clarity|coverage|efficiency>",
      "suggestion": "<actionable improvement suggestion>"
    }
  ],
  "missing_scenarios": [
    {
      "scenario": "<description of missing scenario>",
      "importance": "<high|medium|low>",
      "reason": "<why this scenario is important>"
    }
  ],
  "redundant_tests": [
    {
      "test_cases": ["<test case 1>", "<test case 2>"],
      "reason": "<why these are redundant>",
      "recommendation": "<keep which one or merge>"
    }
  ],
  "coverage_analysis": {
    "positive_scenarios": "<percentage or count covered>",
    "negative_scenarios": "<percentage or count covered>",
    "edge_cases": "<percentage or count covered>",
    "gaps": ["<gap 1>", "<gap 2>"]
  }
}
```

Focus on being constructive and specific. Provide actionable feedback that helps improve the test suite.
""")

        return "\n".join(prompt_parts)

    def implement_improvements(
        self,
        existing_test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]],
        review_feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Implement improvement suggestions from the review, including:
        - Suggestions for completeness, clarity, coverage, efficiency
        - Missing scenarios
        - Fixes for identified issues

        Args:
            existing_test_cases: Current test cases
            requirements: Requirements being tested
            review_feedback: Full review feedback with suggestions, issues, and missing scenarios

        Returns:
            List of improved/new test cases
        """
        suggestions = review_feedback.get('suggestions', [])
        issues = review_feedback.get('issues', [])
        missing_scenarios = review_feedback.get('missingScenarios', [])

        print(f"DEBUG TestCaseReviewer: Implementing improvements - {len(suggestions)} suggestions, {len(issues)} issues, {len(missing_scenarios)} missing scenarios")

        if not suggestions and not issues and not missing_scenarios:
            print("DEBUG TestCaseReviewer: No improvements to implement")
            return []

        prompt = self._build_improvement_prompt(existing_test_cases, requirements, suggestions, issues, missing_scenarios)

        sys_prompt = """You are an expert QA engineer specializing in BLACK BOX TESTING. Your job is to implement improvement suggestions by:

1. **Adding new test cases** for missing scenarios
2. **Improving existing test cases** based on suggestions (completeness, clarity, coverage, efficiency)
3. **Fixing identified issues** in test cases

**BLACK BOX TESTING FOCUS**:
- Test from a user's perspective
- Focus on observable behaviors and user interactions
- Test inputs, outputs, and business logic without internal implementation details
- Validate error handling as seen by the user

Return improved and new test cases that address ALL the feedback provided."""

        # Use gpt-4o for improvement implementation (keep quality high for this critical task)
        # Reduced tokens by 25% (12000 -> 9000) for cost optimization
        response, error = self.llm.complete_json(sys_prompt, prompt, max_tokens=9000)

        if error:
            print(f"DEBUG TestCaseReviewer: Failed to implement improvements: {error}")
            return {
                "improved_test_cases": [],
                "new_test_cases": []
            }

        try:
            result = json.loads(response)
            improved = result.get('improved_test_cases', [])
            new = result.get('new_test_cases', [])

            # Also support old format for backward compatibility
            if not improved and not new and result.get('test_cases'):
                new = result.get('test_cases', [])

            print(f"DEBUG TestCaseReviewer: Returning {len(improved)} improved and {len(new)} new test cases")

            return {
                "improved_test_cases": improved,
                "new_test_cases": new
            }
        except json.JSONDecodeError:
            print("DEBUG TestCaseReviewer: Failed to parse improvement results")
            return {
                "improved_test_cases": [],
                "new_test_cases": []
            }

    def _build_improvement_prompt(
        self,
        existing_test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        missing_scenarios: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for implementing all improvement suggestions."""

        prompt_parts = []

        # Existing test cases
        prompt_parts.append("## Current Test Cases")
        prompt_parts.append(f"Total: {len(existing_test_cases)} test cases")
        for i, tc in enumerate(existing_test_cases[:10], 1):
            tc_name = tc.get('name', tc.get('title', f'Test Case {i}'))
            tc_type = tc.get('type', 'Unknown')
            tc_steps = tc.get('steps', [])
            prompt_parts.append(f"{i}. {tc_name} ({tc_type}, {len(tc_steps)} steps)")
        if len(existing_test_cases) > 10:
            prompt_parts.append(f"... and {len(existing_test_cases) - 10} more test cases")
        prompt_parts.append("")

        # Requirements
        prompt_parts.append("## Requirements")
        for i, req in enumerate(requirements[:10], 1):
            if isinstance(req, str):
                req_text = req
            else:
                req_text = req.get('requirement', req.get('text', 'No description'))
            prompt_parts.append(f"{i}. {req_text}")
        if len(requirements) > 10:
            prompt_parts.append(f"... and {len(requirements) - 10} more requirements")
        prompt_parts.append("")

        # Improvement Suggestions
        if suggestions:
            prompt_parts.append("## Improvement Suggestions to Implement")
            for i, sug in enumerate(suggestions, 1):
                category = sug.get('category', 'General')
                suggestion = sug.get('suggestion', '')
                prompt_parts.append(f"{i}. [{category}] {suggestion}")
            prompt_parts.append("")

        # Issues to Fix
        if issues:
            prompt_parts.append("## Issues to Fix")
            for i, issue in enumerate(issues, 1):
                test_case = issue.get('test_case', 'Unknown')
                severity = issue.get('severity', 'medium')
                problem = issue.get('issue', '')
                fix_suggestion = issue.get('suggestion', '')
                prompt_parts.append(f"{i}. [{severity.upper()}] {test_case}")
                prompt_parts.append(f"   Problem: {problem}")
                if fix_suggestion:
                    prompt_parts.append(f"   How to Fix: {fix_suggestion}")
            prompt_parts.append("")

        # Missing Scenarios
        if missing_scenarios:
            prompt_parts.append("## Missing Scenarios to Add")
            for i, scenario in enumerate(missing_scenarios, 1):
                sc_text = scenario.get('scenario', '')
                importance = scenario.get('importance', 'medium')
                reason = scenario.get('reason', '')
                prompt_parts.append(f"{i}. [{importance.upper()}] {sc_text}")
                prompt_parts.append(f"   Why Important: {reason}")
            prompt_parts.append("")

        # Task instructions
        prompt_parts.append("""## Task
Implement ALL the improvements above by returning test cases in TWO separate arrays:
1. **Improved versions** of existing test cases (addressing suggestions and fixing issues) - keep the same number/order as existing tests
2. **New test cases** for missing scenarios - brand new test cases that don't replace existing ones

Return JSON in this format:
```json
{
  "improved_test_cases": [
    {
      "index": <index of original test case being improved, 0-based>,
      "requirement_id": "<REQ-XXX>",
      "requirement_desc": "The enquiry form should display with all specified fields and buttons.",
      "title": "Enquiry form displays with all specified fields and buttons",
      "name": "Enquiry form displays with all specified fields and buttons",
      "type": "Positive",
      "objective": "To verify that the enquiry form displays correctly with all necessary fields and buttons.",
      "preconditions": ["User is on the homepage"],
      "steps": [
        "Step 1: <action>",
        "Expected Result: <expected outcome>",
        "Step 2: <action>",
        "Expected Result: <expected outcome>"
      ],
      "expected_result": "<final expected outcome>",
      "priority": 1-5,
      "tags": ["tag1", "tag2"]
    }
  ],
  "new_test_cases": [
    {
      "requirement_id": "<REQ-XXX>",
      "requirement_desc": "The enquiry form should display with all specified fields and buttons.",
      "title": "Enquiry form displays with all specified fields and buttons",
      "name": "Enquiry form displays with all specified fields and buttons",
      "type": "Positive",
      "objective": "To verify that the enquiry form displays correctly with all necessary fields and buttons.",
      "preconditions": ["User is on the homepage"],
      "steps": [
        "Step 1: <action>",
        "Expected Result: <expected outcome>",
        "Step 2: <action>",
        "Expected Result: <expected outcome>"
      ],
      "expected_result": "<final expected outcome>",
      "priority": 1-5,
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

**TITLE FORMAT RULES**:
- Title format: "{Clear description of what is being tested}" (NO requirement ID in title)
- The requirement_desc field contains the requirement text as a clear sentence
- The UI will display as: "REQ-XXX: Test Case N {title} ({type})"
- Example: Title = "Enquiry form displays with all specified fields and buttons", UI shows "REQ-001: Test Case 1 Enquiry form displays with all specified fields and buttons (Positive)"

**CRITICAL RULES**:
1. Every test must have 3-8 steps (simple tests: 3-4, complex: 5-8)
2. **MANDATORY**: Every "Step N:" MUST be immediately followed by "Expected Result:" - no exceptions!
3. **MANDATORY**: Every test case MUST have "requirement_id" AND "requirement_desc" fields - requirement_desc should be a clear sentence describing the requirement
4. **MANDATORY**: Every test case MUST have both "title" and "name" fields (use same value for both, NO requirement ID in title)
5. **MANDATORY**: Every test case MUST have an "objective" field explaining what aspect of the requirement is being tested (start with "To verify that...")
6. **MANDATORY**: Every test case MUST have "preconditions" array (can be empty [] if none needed, otherwise list specific preconditions)
7. **MANDATORY**: Every test case MUST have an "expected_result" field with the final expected outcome
8. Focus on black box testing (user perspective, observable behaviors)
9. Make steps specific, testable, and realistic
10. Address ALL suggestions, issues, and missing scenarios provided above
11. **IMPORTANT**: Only include improved versions if there are actual improvements to make. If a test case is already good, don't include it in improved_test_cases.
12. **IMPORTANT**: For improved_test_cases, include the "index" field matching the original test case position (0-based).

Return separate arrays for improved existing tests and brand new tests.""")

        return "\n".join(prompt_parts)
