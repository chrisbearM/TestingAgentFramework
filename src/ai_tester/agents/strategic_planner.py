"""
Strategic Planner Agent
Proposes different strategic approaches for splitting Epics into test tickets
"""

from typing import Dict, List, Any, Tuple, Optional
import json
from .base_agent import BaseAgent


class StrategicPlannerAgent(BaseAgent):
    """
    Analyzes an Epic and proposes 3 fundamentally different strategic approaches
    to split it into manageable test tickets for a QA team.
    """

    def run(self, context: Dict[str, Any], **kwargs) -> Tuple[List[Dict], Optional[str]]:
        """
        Generate strategic split options for an Epic

        Args:
            context: Dictionary containing:
                - epic_key: Epic identifier (e.g., "UEX-123")
                - epic_summary: Epic title/summary
                - epic_desc: Epic description (optional)
                - children: List of child ticket dictionaries with keys:
                    - key: Ticket identifier
                    - summary: Ticket summary
                    - desc: Ticket description (optional)

        Returns:
            Tuple of (options_list, error) where options_list contains 3 strategic approaches
        """
        return self.propose_splits(context)

    def propose_splits(self, epic_context: Dict[str, Any]) -> Tuple[List[Dict], Optional[str]]:
        """
        Generate 3 strategic approaches for splitting the Epic

        Args:
            epic_context: Epic and child ticket information

        Returns:
            Tuple of (options_list, error) with 3 strategic options or error message
        """
        system_prompt = """You are a senior test architect with 15 years of experience in software testing and QA team management.

Your expertise includes:
- Designing comprehensive test strategies for complex software projects
- Optimizing test execution and team workflow
- Balancing thoroughness with practicality
- Identifying critical testing paths and risk areas

Given an Epic with child tickets, your task is to propose 3 FUNDAMENTALLY DIFFERENT strategic approaches to split this into test tickets for a QA team.

PROVEN SPLITTING STRATEGIES:
1. User Journey: Group by end-to-end user flows and scenarios
2. Technical Layer: Group by system layer (UI, API, Database, Integration)
3. Risk-Based: Group by criticality (Critical Path, High Risk, Edge Cases)
4. Functional Area: Group by feature domains or business capabilities
5. Test Type: Group by test category (Functional, Security, Performance, Integration)
6. Complexity: Group by simple vs complex scenarios

CRITICAL REQUIREMENTS:
- Each approach should result in 2-5 manageable test tickets
- Each test ticket should cover 15-30 test cases (estimate)
- Approaches must be DISTINCTLY DIFFERENT from each other
- Each ticket should be independently executable
- Minimize dependencies between test tickets where possible

OUTPUT FORMAT:
You must return ONLY valid JSON with this exact structure:
{
  "options": [
    {
      "name": "Split by User Journey",
      "rationale": "Detailed explanation of why this approach fits this specific Epic. Reference specific child tickets.",
      "advantages": [
        "Advantage 1 specific to this Epic",
        "Advantage 2 specific to this Epic",
        "Advantage 3 specific to this Epic"
      ],
      "disadvantages": [
        "Disadvantage 1 specific to this approach",
        "Disadvantage 2 specific to this approach"
      ],
      "tickets": [
        {
          "title": "Test Ticket: [Descriptive Title]",
          "scope": "Covers child tickets: EPIC-101, EPIC-102, EPIC-105",
          "description": "Detailed description of what this test ticket covers",
          "estimated_test_cases": 22,
          "priority": "Critical|High|Medium",
          "focus_areas": ["Area 1", "Area 2", "Area 3"]
        }
      ]
    }
  ]
}"""

        # Build child tickets summary
        children = epic_context.get('children') or []
        children_summary = self._format_children(children)

        # Build attachments summary
        epic_attachments = epic_context.get('epic_attachments', [])
        child_attachments = epic_context.get('child_attachments', {})
        attachments_summary = self._format_attachments(epic_attachments, child_attachments)

        user_prompt = f"""Analyze this Epic and propose 3 different strategic approaches for splitting it into test tickets:

EPIC DETAILS:
Epic Key: {epic_context.get('epic_key', 'N/A')}
Epic Summary: {epic_context.get('epic_summary', 'N/A')}

Epic Description:
{(epic_context.get('epic_desc', 'No description provided') or 'No description provided')[:1000]}

{attachments_summary}

CHILD TICKETS ({len(children)}):
{children_summary}

TASK:
Propose 3 fundamentally different strategic approaches to split this Epic into test tickets.

Each approach should:
1. Propose 2-5 test tickets
2. Each ticket should cover 15-30 test cases (estimate)
3. Map child tickets to test tickets clearly
4. Have distinct advantages for this specific Epic
5. Be independently executable by QA team members

Consider:
- What is the natural grouping for these child tickets?
- What approach minimizes dependencies?
- What approach provides best test coverage?
- What approach is most practical for parallel execution?

Return ONLY valid JSON following the exact structure specified in the system prompt."""

        # Call LLM
        result, error = self._call_llm(system_prompt, user_prompt, max_tokens=4000)

        if error:
            return [], self._format_error(f"Failed to generate split options: {error}")

        # Parse response
        parsed = self._parse_json_response(result)

        if not parsed or 'options' not in parsed:
            return [], self._format_error("Invalid response format - missing 'options' key")

        options = parsed.get('options') or []

        if len(options) < 3:
            return [], self._format_error(f"Expected 3 options, got {len(options)}")

        # Validate each option
        for i, option in enumerate(options):
            if not self._validate_option(option):
                return [], self._format_error(f"Option {i+1} has invalid structure")

        return options, None

    def _format_children(self, children: List[Dict]) -> str:
        """
        Format child tickets for inclusion in prompt

        Args:
            children: List of child ticket dictionaries

        Returns:
            Formatted string representation of child tickets
        """
        if not children:
            return "No child tickets"

        output = []
        # Limit to first 30 to avoid token limits
        for child in children[:30]:
            key = child.get('key', 'N/A')
            summary = child.get('summary', 'No summary')
            desc = child.get('desc') or ''

            # Truncate description
            desc_preview = desc[:150] + "..." if len(desc) > 150 else desc

            output.append(f"- {key}: {summary}")
            if desc_preview:
                output.append(f"  Description: {desc_preview}")

        if len(children) > 30:
            output.append(f"\n... and {len(children) - 30} more child tickets")

        return "\n".join(output)

    def _format_attachments(self, epic_attachments: List[Dict], child_attachments: Dict[str, List[Dict]]) -> str:
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

        output = ["ATTACHMENTS:"]

        # Epic attachments
        if epic_attachments:
            output.append("\nEpic Attachments:")
            for att in epic_attachments:
                filename = att.get('filename', 'Unknown')
                att_type = att.get('type', 'unknown')

                if att_type == 'image':
                    output.append(f"  • {filename} (UI Mockup/Screenshot)")
                    output.append(f"    → This image shows visual/UI requirements that should be tested")
                elif att_type == 'document':
                    content = att.get('content', '')
                    preview = content[:300] + "..." if len(content) > 300 else content
                    output.append(f"  • {filename} (Document)")
                    if preview:
                        output.append(f"    Content preview: {preview}")

        # Child ticket attachments
        if child_attachments:
            output.append("\nChild Ticket Attachments:")
            for child_key, attachments in list(child_attachments.items())[:10]:  # Limit to first 10
                output.append(f"  {child_key}:")
                for att in attachments:
                    filename = att.get('filename', 'Unknown')
                    att_type = att.get('type', 'unknown')

                    if att_type == 'image':
                        output.append(f"    • {filename} (UI Mockup/Screenshot)")
                    elif att_type == 'document':
                        output.append(f"    • {filename} (Document)")

        output.append("\nNOTE: Pay special attention to UI mockups and screenshots - these indicate visual/interface testing requirements.\n")

        return "\n".join(output)

    def _validate_option(self, option: Dict) -> bool:
        """
        Validate that an option has the required structure

        Args:
            option: Option dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_keys = ['name', 'rationale', 'advantages', 'disadvantages', 'tickets']

        for key in required_keys:
            if key not in option:
                return False

        # Validate tickets structure
        tickets = option.get('tickets') or []
        if not tickets:
            return False

        for ticket in tickets:
            required_ticket_keys = ['title', 'scope', 'description', 'estimated_test_cases', 'priority', 'focus_areas']
            for key in required_ticket_keys:
                if key not in ticket:
                    return False

        return True
