"""
Strategic Planner Agent v2.0
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

    def propose_splits(self, epic_context: Dict[str, Any], pre_analyzed_attachments: Dict[str, Any] = None) -> Tuple[List[Dict], Optional[str]]:
        """
        Generate 3 strategic approaches for splitting the Epic

        Args:
            epic_context: Epic and child ticket information
            pre_analyzed_attachments: Optional pre-analyzed attachment data (for parallel execution)

        Returns:
            Tuple of (options_list, error) with 3 strategic options or error message
        """
        system_prompt = """You are a senior test architect with 15 years of experience in software testing and QA team management.

Your expertise includes:
- Designing comprehensive test strategies for complex software projects
- Optimizing test execution and team workflow
- Balancing thoroughness with practicality
- Identifying critical testing paths and risk areas
- Creating UI/UX test plans from mockups and wireframes

Given an Epic with child tickets, your task is to propose 3 FUNDAMENTALLY DIFFERENT strategic approaches to split this into test tickets for a QA team.

IMPORTANT: If UI mockups, screenshots, or design documents are provided in the attachments:
- Analyze them carefully and extract specific UI elements, workflows, and features
- Create dedicated test tickets for UI/visual testing based on the mockups
- Include specific UI elements (buttons, forms, menus, navigation) in test ticket descriptions
- Ensure visual testing requirements are not overlooked

PROVEN SPLITTING STRATEGIES:
1. User Journey: Group by end-to-end user flows and scenarios
2. Technical Layer: Group by system layer (UI, API, Database, Integration)
3. Risk-Based: Group by criticality (Critical Path, High Risk, Edge Cases)
4. Functional Area: Group by feature domains or business capabilities
5. Test Type: Group by test category (Functional, Security, Performance, Integration, UI/Visual)
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
      "test_tickets": [
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

        # Build attachments summary (use pre-analyzed data if available)
        epic_attachments = epic_context.get('epic_attachments', [])
        child_attachments = epic_context.get('child_attachments', {})
        attachments_summary = self._format_attachments(epic_attachments, child_attachments, pre_analyzed_attachments)

        print(f"DEBUG Strategic Planner: Processing {len(epic_attachments)} epic attachments")
        if pre_analyzed_attachments:
            print(f"DEBUG: Using pre-analyzed attachment data")
        for att in epic_attachments:
            att_type = att.get('type', 'unknown')
            filename = att.get('filename', 'Unknown')
            if att_type == 'document':
                content_len = len(att.get('content', ''))
                print(f"  - {filename} ({att_type}): {content_len} characters of text")
            elif att_type == 'image':
                print(f"  - {filename} ({att_type}): base64 encoded")
        print(f"DEBUG: Attachments summary length: {len(attachments_summary)} characters")

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

CRITICAL: If UI mockups or screenshots are provided above in the attachments:
- Reference specific UI elements mentioned in the vision analysis
- Create test tickets that specifically cover the visual/UI aspects shown in the mockups
- Include UI element names, buttons, forms, navigation flows in your test ticket descriptions
- Ensure at least ONE of the three strategies includes a dedicated UI/Visual testing approach

Consider:
- What is the natural grouping for these child tickets?
- What approach minimizes dependencies?
- What approach provides best test coverage?
- What approach is most practical for parallel execution?
- How can we leverage the uploaded documents and images to create more comprehensive test tickets?

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

        # Validate each option and transform if needed for compatibility
        for i, option in enumerate(options):
            print(f"DEBUG: Processing option {i+1}")
            print(f"DEBUG: Option keys before transform: {list(option.keys())}")

            # Compatibility: transform 'tickets' to 'test_tickets' if LLM returns old format
            if 'tickets' in option and 'test_tickets' not in option:
                print(f"DEBUG: Transforming 'tickets' to 'test_tickets' for option {i+1}")
                print(f"DEBUG: Found {len(option['tickets'])} tickets to transform")
                option['test_tickets'] = option['tickets']
                del option['tickets']
            elif 'test_tickets' in option:
                print(f"DEBUG: Option {i+1} already has 'test_tickets' field with {len(option['test_tickets'])} items")
            else:
                print(f"DEBUG: WARNING - Option {i+1} has neither 'tickets' nor 'test_tickets'!")

            print(f"DEBUG: Option keys after transform: {list(option.keys())}")

            if not self._validate_option(option):
                print(f"DEBUG: Validation failed for option {i+1}")
                print(f"DEBUG: Option structure:")
                for key, value in option.items():
                    if isinstance(value, list):
                        print(f"DEBUG:   {key}: list with {len(value)} items")
                    else:
                        print(f"DEBUG:   {key}: {type(value).__name__}")
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

    def analyze_attachments(self, epic_attachments: List[Dict], child_attachments: Dict[str, List[Dict]] = None) -> Dict[str, Any]:
        """
        Analyze attachments (images and documents) separately from formatting.
        This can be called asynchronously before strategic planning.

        Args:
            epic_attachments: List of epic attachment dictionaries
            child_attachments: Dict mapping child ticket keys to their attachments

        Returns:
            Dictionary containing image_analysis results and document summaries
        """
        if child_attachments is None:
            child_attachments = {}

        result = {
            "image_analysis": {},
            "document_summaries": {},
            "analysis_complete": True
        }

        if not epic_attachments:
            return result

        # Analyze all images in batch using vision API
        image_attachments = [att for att in epic_attachments if att.get('type') == 'image']

        print(f"DEBUG: Found {len(image_attachments)} image attachments for analysis")

        if image_attachments and hasattr(self, 'llm') and self.llm:
            try:
                # Analyze images in batches (max 3 at a time to avoid token limits)
                for i in range(0, len(image_attachments), 3):
                    batch = image_attachments[i:i+3]
                    batch_names = [att.get('filename', 'Unknown') for att in batch]

                    print(f"DEBUG: Analyzing {len(batch)} images: {batch_names}")
                    analysis = self.llm.analyze_images(
                        batch,
                        "UI mockups and screenshots for test planning. Describe the UI elements, workflows, and features visible in each image."
                    )
                    print(f"DEBUG: Vision API returned {len(analysis)} characters of analysis")

                    # Store analysis for each image in the batch
                    for att in batch:
                        result["image_analysis"][att.get('filename')] = analysis
                        print(f"DEBUG: Stored analysis for {att.get('filename')}")

            except Exception as e:
                print(f"DEBUG: Failed to analyze images: {e}")
                result["analysis_complete"] = False

        # Pre-process document content
        for att in epic_attachments:
            if att.get('type') == 'document':
                filename = att.get('filename', 'Unknown')
                content = att.get('content', '')
                # Store preview for later use
                result["document_summaries"][filename] = content[:2000] + "..." if len(content) > 2000 else content

        return result

    def _format_attachments(self, epic_attachments: List[Dict], child_attachments: Dict[str, List[Dict]], pre_analyzed: Dict[str, Any] = None) -> str:
        """
        Format attachments for inclusion in prompt.

        Args:
            epic_attachments: List of epic attachment dictionaries
            child_attachments: Dict mapping child ticket keys to their attachments
            pre_analyzed: Optional pre-analyzed attachment data (from analyze_attachments)

        Returns:
            Formatted string representation of attachments
        """
        if not epic_attachments and not child_attachments:
            return ""

        # Use pre-analyzed data if available, otherwise analyze inline (backward compatibility)
        if pre_analyzed is None:
            pre_analyzed = self.analyze_attachments(epic_attachments, child_attachments)

        image_analysis = pre_analyzed.get("image_analysis", {})
        document_summaries = pre_analyzed.get("document_summaries", {})

        output = ["ATTACHMENTS:"]

        # Epic attachments
        if epic_attachments:
            output.append("\nEpic Attachments:")

            print(f"DEBUG: Formatting {len(epic_attachments)} epic attachments")
            print(f"DEBUG: Pre-analyzed images: {len(image_analysis)}, documents: {len(document_summaries)}")

            for att in epic_attachments:
                filename = att.get('filename', 'Unknown')
                att_type = att.get('type', 'unknown')

                if att_type == 'image':
                    output.append(f"  • {filename} (UI Mockup/Screenshot)")
                    if filename in image_analysis:
                        output.append(f"    AI Vision Analysis: {image_analysis[filename][:500]}...")
                    else:
                        output.append(f"    → This image shows visual/UI requirements that should be tested")
                elif att_type == 'document':
                    output.append(f"  • {filename} (Document)")
                    if filename in document_summaries:
                        preview = document_summaries[filename]
                        output.append(f"    Content: {preview}")
                        print(f"DEBUG: Including {len(preview)} chars from {filename}")
                    else:
                        content = att.get('content', '')
                        preview = content[:2000] + "..." if len(content) > 2000 else content
                        if preview:
                            output.append(f"    Content: {preview}")

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
        required_keys = ['name', 'rationale', 'advantages', 'disadvantages', 'test_tickets']

        for key in required_keys:
            if key not in option:
                return False

        # Validate tickets structure
        tickets = option.get('test_tickets') or []
        if not tickets:
            return False

        for ticket in tickets:
            required_ticket_keys = ['title', 'scope', 'description', 'estimated_test_cases', 'priority', 'focus_areas']
            for key in required_ticket_keys:
                if key not in ticket:
                    return False

        return True
