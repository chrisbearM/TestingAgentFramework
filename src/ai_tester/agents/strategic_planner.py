"""
Strategic Planner Agent v2.0
Proposes different strategic approaches for splitting Epics into test tickets
"""

from typing import Dict, List, Any, Tuple, Optional
import json
from pydantic import BaseModel, Field
from .base_agent import BaseAgent
from ai_tester.utils.token_manager import validate_prompt_size, truncate_to_token_limit, estimate_tokens


# Pydantic models for structured output
class TestTicket(BaseModel):
    """Schema for a test ticket in a strategic option"""
    title: str = Field(description="Test ticket title starting with 'Test: '")
    scope: str = Field(description="Scope description indicating which child tickets are covered (e.g., 'Covers: KEY-1, KEY-2')")
    description: str = Field(description="Detailed description of what this test ticket covers")
    estimated_test_cases: int = Field(description="Estimated number of test cases (15-30)", ge=15, le=30)
    priority: str = Field(description="Priority level: Critical, High, or Medium")
    focus_areas: List[str] = Field(description="List of key focus areas for testing")


class StrategicOption(BaseModel):
    """Schema for a single strategic split option"""
    name: str = Field(description="Name of the split strategy (e.g., 'Split by User Journey')")
    rationale: str = Field(description="Why this strategy is good for this Epic, including how child tickets map to test tickets")
    advantages: List[str] = Field(description="List of advantages of this approach")
    disadvantages: List[str] = Field(description="List of disadvantages or limitations")
    test_tickets: List[TestTicket] = Field(description="List of 2-5 test tickets for this strategy")


class StrategicPlanResponse(BaseModel):
    """Complete response schema for strategic planning"""
    options: List[StrategicOption] = Field(description="List of exactly 3 strategic split options", min_length=3, max_length=3)


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

    def propose_splits(self, epic_context: Dict[str, Any], pre_analyzed_attachments: Dict[str, Any] = None, use_structured_output: bool = True) -> Tuple[List[Dict], Optional[str]]:
        """
        Generate 3 strategic approaches for splitting the Epic

        Args:
            epic_context: Epic and child ticket information
            pre_analyzed_attachments: Optional pre-analyzed attachment data (for parallel execution)
            use_structured_output: Whether to use OpenAI structured outputs (default: True)

        Returns:
            Tuple of (options_list, error) with 3 strategic options or error message
        """
        system_prompt = """Senior test architect. Propose 3 DIFFERENT Epic split strategies.

STRATEGIES:
User Journey|Technical Layer|Risk-Based|Functional Area|Test Type|Complexity

MOCKUPS/DOCS: Create dedicated UI test tickets with specific elements

RULES:
- 2-5 tickets per approach
- 15-30 test cases/ticket
- Independent, minimal dependencies

JSON:
{
  "options": [{
    "name": "Split by X",
    "rationale": "Why + child tickets",
    "advantages": ["..."],
    "disadvantages": ["..."],
    "test_tickets": [{
      "title": "Test: [Title]",
      "scope": "Covers: KEY-1, KEY-2",
      "description": "...",
      "estimated_test_cases": 22,
      "priority": "Critical|High|Medium",
      "focus_areas": ["..."]
    }]
  }]
}

IMPORTANT DATA HANDLING:
- Focus on functional requirements and test scenarios only
- Do NOT generate, request, or repeat specific user identities (names, emails, usernames)
- Do NOT generate or request sensitive internal data (credentials, API keys, secrets)
- If input contains potentially sensitive data, reference it generically without repeating verbatim
- Prioritize test coverage and quality over metadata

""" + BaseAgent.get_accuracy_principles()

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

        # Validate token limits before calling LLM (C8 Fix)
        model = "gpt-4o"  # Default model used by this agent
        validation = validate_prompt_size(system_prompt, user_prompt, model=model, response_reserve=4000)

        if not validation["valid"]:
            print(f"WARNING: Prompt exceeds token limit!")
            print(f"  Total tokens: {validation['total_tokens']}")
            print(f"  Max allowed: {validation['max_allowed']}")
            print(f"  Exceeds by: {validation['exceeds_by']}")

            # Truncate user prompt to fit within limits
            # Reserve space for system prompt + overhead
            max_user_tokens = validation['max_allowed'] - validation['system_tokens'] - 100

            print(f"  Truncating user prompt to {max_user_tokens} tokens...")
            user_prompt = truncate_to_token_limit(
                user_prompt,
                max_tokens=max_user_tokens,
                model=model,
                truncation_strategy="end",
                preserve_structure=True
            )

            # Re-validate after truncation
            new_validation = validate_prompt_size(system_prompt, user_prompt, model=model, response_reserve=4000)
            print(f"  After truncation: {new_validation['total_tokens']} tokens (valid: {new_validation['valid']})")

        # Call LLM with or without structured output
        if use_structured_output:
            result, error = self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=4000
            )

            if error:
                return [], self._format_error(f"Failed to generate split options: {error}")

            # Extract options from structured response
            options = result.get('options', [])

            # Validate each option
            for i, option in enumerate(options):
                print(f"DEBUG: Processing option {i+1}")
                print(f"DEBUG: Option keys: {list(option.keys())}")

                if not self._validate_option(option):
                    print(f"DEBUG: Validation failed for option {i+1}")
                    return [], self._format_error(f"Option {i+1} has invalid structure")

            return options, None
        else:
            # Fallback to regular JSON mode
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

    def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Call LLM with structured output using Pydantic model

        Args:
            system_prompt: System prompt defining the agent's role
            user_prompt: User prompt with specific task details
            max_tokens: Maximum tokens for the response

        Returns:
            Tuple of (result dict, error message)
        """
        try:
            result, error = self.llm.complete_json(
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
                pydantic_model=StrategicPlanResponse
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
