"""
Evaluation Agent
Scores strategic split options on multiple quality dimensions
"""

from typing import Dict, Any, Tuple, Optional
import json
from .base_agent import BaseAgent


class EvaluationAgent(BaseAgent):
    """
    Evaluates strategic split options and provides scores across multiple dimensions:
    - Testability: How easy is it to test each ticket?
    - Coverage: How well does it cover all requirements?
    - Manageability: How manageable is each ticket size?
    - Independence: How independent are tickets from each other?
    - Parallel Execution: How well can tickets run in parallel?
    """

    def run(self, context: Dict[str, Any], **kwargs) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Evaluate a strategic split option

        Args:
            context: Dictionary containing:
                - option: The strategic option to evaluate
                - epic_context: Original Epic context with children

        Returns:
            Tuple of (scores_dict, error)
        """
        option = context.get('option')
        epic_context = context.get('epic_context')

        if not option or not epic_context:
            return {}, self._format_error("Missing required context: option and epic_context")

        return self.evaluate_split(option, epic_context)

    def evaluate_split(self, split_option: Dict[str, Any],
                       epic_context: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Evaluate a strategic split option

        Args:
            split_option: The strategic option to evaluate (from StrategicPlannerAgent)
            epic_context: Original Epic and child ticket information

        Returns:
            Tuple of (evaluation_dict, error) with scores on multiple dimensions
        """
        system_prompt = """You are a senior QA evaluation expert who scores test strategies objectively.

Your role is to evaluate a proposed strategic split of an Epic into test tickets across 5 key dimensions:

1. TESTABILITY (0-10): How easy is it to create and execute tests for each ticket?
   - Clear scope and boundaries = higher score
   - Vague or overlapping scope = lower score
   - Well-defined test focus = higher score

2. COVERAGE (0-10): How well does the split cover all child tickets and requirements?
   - All child tickets mapped = 10
   - Some gaps = 5-7
   - Major gaps = 0-4

3. MANAGEABILITY (0-10): How manageable is each test ticket?
   - 15-30 test cases per ticket = optimal (8-10)
   - 5-15 test cases = too small (5-7)
   - 30-50 test cases = acceptable (6-8)
   - 50+ test cases = too large (0-5)

4. INDEPENDENCE (0-10): How independent are test tickets from each other?
   - No dependencies between tickets = 10
   - Some dependencies = 5-7
   - High dependencies = 0-4

5. PARALLEL EXECUTION (0-10): How well can tickets be executed in parallel?
   - All tickets can run simultaneously = 10
   - Some sequential requirements = 5-7
   - Must run mostly sequentially = 0-4

Additionally, provide:
- OVERALL SCORE (0-10): Weighted average of all dimensions
- RECOMMENDATION: Short 1-2 sentence recommendation
- CONCERNS: List of specific concerns or risks

OUTPUT FORMAT:
Return ONLY valid JSON:
{
  "testability": 8,
  "testability_notes": "Clear ticket boundaries make test creation straightforward",
  "coverage": 9,
  "coverage_notes": "All child tickets are mapped, minor overlap acceptable",
  "manageability": 7,
  "manageability_notes": "Ticket sizes range from 18-35 test cases, mostly good",
  "independence": 9,
  "independence_notes": "Tickets can be tested independently with minimal setup",
  "parallel_execution": 10,
  "parallel_execution_notes": "All tickets can run in parallel without conflicts",
  "overall": 8.6,
  "recommendation": "Strong strategic option with excellent parallel execution and independence.",
  "concerns": [
    "Ticket 3 might be slightly large at 35 estimated test cases",
    "Minor overlap between Ticket 1 and 2 in user registration flow"
  ]
}"""

        # Build evaluation prompt
        option_name = split_option.get('name', 'Unknown')
        rationale = split_option.get('rationale', 'N/A')
        # Support both 'test_tickets' (new format) and 'tickets' (legacy format)
        tickets = split_option.get('test_tickets') or split_option.get('tickets') or []
        children = epic_context.get('children') or []

        tickets_summary = self._format_tickets(tickets)
        children_keys = [child.get('key') for child in children]

        user_prompt = f"""Evaluate this strategic split option:

STRATEGIC OPTION:
Name: {option_name}
Rationale: {rationale}

PROPOSED TEST TICKETS ({len(tickets)}):
{tickets_summary}

EPIC CONTEXT:
Epic: {epic_context.get('epic_key')} - {epic_context.get('epic_summary')}
Total Child Tickets: {len(children)}
Child Ticket Keys: {', '.join(children_keys[:30])}{"..." if len(children_keys) > 30 else ""}

TASK:
Evaluate this strategic option across all 5 dimensions:
1. Testability (0-10)
2. Coverage (0-10)
3. Manageability (0-10)
4. Independence (0-10)
5. Parallel Execution (0-10)

For each dimension:
- Provide a numeric score (0-10)
- Provide specific notes explaining the score

Then provide:
- Overall weighted score (0-10)
- Recommendation (1-2 sentences)
- List of specific concerns (if any)

Return ONLY valid JSON following the exact structure in the system prompt."""

        # Call LLM
        result, error = self._call_llm(system_prompt, user_prompt, max_tokens=1500)

        if error:
            return {}, self._format_error(f"Failed to evaluate split: {error}")

        # Parse response
        parsed = self._parse_json_response(result)

        if not parsed:
            return {}, self._format_error("Invalid response format")

        # Validate scores
        if not self._validate_scores(parsed):
            return {}, self._format_error("Invalid score structure")

        return parsed, None

    def _format_tickets(self, tickets: list) -> str:
        """
        Format proposed tickets for evaluation prompt

        Args:
            tickets: List of proposed test ticket dictionaries

        Returns:
            Formatted string representation
        """
        if not tickets or tickets is None:
            return "No tickets proposed"

        output = []
        for i, ticket in enumerate(tickets, 1):
            title = ticket.get('title', 'Untitled')
            scope = ticket.get('scope', 'N/A')
            description = ticket.get('description', 'N/A')
            est_cases = ticket.get('estimated_test_cases', 0)
            priority = ticket.get('priority', 'N/A')
            focus = ', '.join(ticket.get('focus_areas', []))

            output.append(f"""
Ticket {i}: {title}
  Scope: {scope}
  Description: {description[:200]}{"..." if len(description) > 200 else ""}
  Estimated Test Cases: {est_cases}
  Priority: {priority}
  Focus Areas: {focus}
""")

        return "\n".join(output)

    def _validate_scores(self, evaluation: Dict) -> bool:
        """
        Validate that evaluation has required scores

        Args:
            evaluation: Evaluation dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_keys = [
            'testability', 'testability_notes',
            'coverage', 'coverage_notes',
            'manageability', 'manageability_notes',
            'independence', 'independence_notes',
            'parallel_execution', 'parallel_execution_notes',
            'overall', 'recommendation', 'concerns'
        ]

        for key in required_keys:
            if key not in evaluation:
                return False

        # Validate score ranges
        score_keys = ['testability', 'coverage', 'manageability', 'independence', 'parallel_execution', 'overall']
        for key in score_keys:
            score = evaluation.get(key)
            if not isinstance(score, (int, float)) or not (0 <= score <= 10):
                return False

        return True
