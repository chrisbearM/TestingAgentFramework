"""
Ticket Analyzer Agent - Assesses ticket readiness for test case generation.
"""

import json
from typing import Dict, List, Optional
from ai_tester.clients.llm_client import LLMClient


class TicketAnalyzerAgent:
    """Agent that analyzes ticket quality and readiness for test case generation."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the analyzer agent.

        Args:
            llm_client: LLM client for making API calls
        """
        self.llm_client = llm_client

    def analyze_ticket(
        self,
        ticket: Dict,
        attachments: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Analyze a Jira ticket for test case generation readiness.

        Args:
            ticket: Jira ticket data
            attachments: Optional list of processed attachments

        Returns:
            Assessment dictionary with score, feedback, and recommendations
        """
        fields = ticket.get("fields", {})
        summary = fields.get("summary", "")
        description = self._extract_description(fields.get("description"))

        # Extract acceptance criteria if present
        ac_blocks = self._extract_acceptance_criteria(description)

        system_prompt = (
            "You are a senior QA engineer assessing ticket quality and readiness for test case creation. "
            "Evaluate whether the ticket has sufficient information to generate high-quality, comprehensive test cases.\n"
            "IMPORTANT: Acceptance criteria and requirements may be embedded within the description, not explicitly labeled. "
            "Look for implicit requirements, expected behaviors, validation rules, and testable conditions throughout the ticket.\n"
            "Output ONLY JSON with this structure:\n"
            '{ "score": string (one of: "Excellent", "Good", "Poor"), '
            '"confidence": number (0-100), '
            '"summary": string (2-3 sentences overall assessment), '
            '"strengths": [string] (what is present and clear), '
            '"missing_elements": [string] (critical gaps in information), '
            '"recommendations": [string] (specific suggestions to improve), '
            '"quality_concerns": [string] (ambiguities or issues), '
            '"implicit_criteria_found": boolean (true if testable criteria exist even without AC section), '
            '"questions_for_author": [string] (specific questions to ask the ticket author), '
            '"ideal_ticket_example": string (a rewritten version of this ticket as it would look if it scored 100%, including all missing elements, clear AC, proper structure) }'
        )

        user_prompt = (
            f"Ticket Summary:\n{summary}\n\n"
            f"Ticket Description:\n{description or '(no description provided)'}\n\n"
            f"Explicit Acceptance Criteria Section:\n{chr(10).join(ac_blocks) if ac_blocks else '(no explicit acceptance criteria section found)'}\n\n"
            "Assess this ticket for test case generation readiness. **Look for testable requirements ANYWHERE in the ticket**, including:\n"
            "- Embedded acceptance criteria within the description (look for 'should', 'must', 'will', 'when', 'then')\n"
            "- Expected behaviors and outcomes described in the story\n"
            "- Validation rules and business logic\n"
            "- User flows and interaction patterns\n"
            "- Data requirements and constraints\n"
            "- Error handling and edge cases mentioned\n"
            "- Visual requirements from attached mockups/diagrams\n"
            "- Requirements from attached documents\n\n"
            "Evaluation Criteria:\n"
            "1. **Requirements Clarity**: Are user needs and system behaviors clear? (can be in description)\n"
            "2. **Testable Conditions**: Are there verifiable, measurable outcomes defined?\n"
            "3. **Behavioral Expectations**: Is expected functionality clearly described?\n"
            "4. **Edge Cases**: Are error states, boundaries, or special conditions mentioned?\n"
            "5. **Context Sufficiency**: Is there enough information to understand the feature?\n"
            "6. **Validation Points**: Can success/failure be objectively determined?\n\n"
            "Scoring Guidelines:\n"
            "- **Excellent (90-100%)**: Clear testable requirements (explicit or implicit), well-defined behaviors, "
            "edge cases considered, sufficient context. AC section is helpful but NOT required if requirements are clear in description.\n"
            "- **Good (70-89%)**: Core requirements and behaviors are clear enough for test creation, but missing some "
            "details like edge cases or validation rules. Testable but could benefit from more specificity.\n"
            "- **Poor (<70%)**: Vague or missing requirements, unclear expected behavior, insufficient detail for "
            "creating meaningful tests, lacks testable conditions.\n\n"
            "Remember: A ticket can score 'Excellent' or 'Good' WITHOUT an explicit AC section if the description "
            "contains clear, testable requirements and expected behaviors.\n\n"
            "Finally, generate:\n"
            "1. Questions for Author: 3-5 specific questions to ask the ticket author:\n"
            "   - Address the missing elements and gaps you identified\n"
            "   - Seek clarification on ambiguous or unclear points\n"
            "   - Request specifics for validation rules, edge cases, or error handling if missing\n"
            "   - Be actionable and help improve the ticket quality\n"
            "   - Be phrased professionally and constructively\n\n"
            "2. Ideal Ticket Example: Rewrite this ticket as it would appear if it scored 100% (Excellent):\n"
            "   - MATCH THE AUTHOR'S WRITING STYLE: Use similar tone, terminology, and structure as the original\n"
            "   - Keep the same voice and formatting preferences (bullets, paragraphs, etc.)\n"
            "   - Include the same core functionality but with all missing elements added\n"
            "   - Add clear, testable acceptance criteria (adapt format to author's style - Given/When/Then if they use it, or their preferred format)\n"
            "   - Include validation rules, edge cases, error handling in the author's voice\n"
            "   - Specify expected behaviors explicitly while maintaining their writing patterns\n"
            "   - Preserve any existing good sections verbatim - only enhance/add what's missing\n"
            "   - Keep it concise but comprehensive - this should feel like the author wrote it, just more complete"
        )

        # Get assessment from LLM
        try:
            json_text, error = self.llm_client.complete_json(system_prompt, user_prompt, max_tokens=2000)

            if error:
                print(f"ERROR: LLM API error: {error}")
                return {
                    "score": "Poor",
                    "confidence": 0,
                    "summary": f"Analysis failed: {error}",
                    "strengths": [],
                    "missing_elements": ["Analysis could not be completed"],
                    "recommendations": ["Please try again"],
                    "quality_concerns": [],
                    "implicit_criteria_found": False,
                    "questions_for_author": [],
                    "ideal_ticket_example": ""
                }

            # Parse JSON response
            result = json.loads(json_text)
            return result
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON response: {e}")
            print(f"Response was: {json_text[:200] if 'json_text' in locals() else 'N/A'}")
            return {
                "score": "Poor",
                "confidence": 0,
                "summary": "Failed to parse analysis response",
                "strengths": [],
                "missing_elements": ["Analysis could not be completed"],
                "recommendations": ["Please try again"],
                "quality_concerns": [],
                "implicit_criteria_found": False,
                "questions_for_author": [],
                "ideal_ticket_example": ""
            }
        except Exception as e:
            print(f"ERROR: Ticket analysis failed: {e}")
            return {
                "score": "Poor",
                "confidence": 0,
                "summary": f"Analysis failed: {str(e)}",
                "strengths": [],
                "missing_elements": ["Analysis could not be completed"],
                "recommendations": ["Please try again"],
                "quality_concerns": [],
                "implicit_criteria_found": False,
                "questions_for_author": [],
                "ideal_ticket_example": ""
            }

    def _extract_description(self, description) -> str:
        """Extract plain text from description (handles ADF format)."""
        if not description:
            return ""

        if isinstance(description, str):
            return description

        # Handle Atlassian Document Format (ADF)
        if isinstance(description, dict) and description.get("type") == "doc":
            return self._adf_to_plaintext(description)

        return str(description)

    def _adf_to_plaintext(self, adf: Dict) -> str:
        """Convert ADF to plain text."""
        if not adf or not adf.get("content"):
            return ""

        text_parts = []
        for node in adf.get("content", []):
            text_parts.append(self._process_node(node))

        return "\n".join(filter(None, text_parts))

    def _process_node(self, node: Dict) -> str:
        """Process a single ADF node."""
        node_type = node.get("type")

        if node_type == "paragraph":
            return self._extract_text_from_content(node.get("content", []))
        elif node_type == "heading":
            text = self._extract_text_from_content(node.get("content", []))
            level = node.get("attrs", {}).get("level", 1)
            return f"{'#' * level} {text}"
        elif node_type in ("bulletList", "orderedList"):
            items = []
            for item in node.get("content", []):
                if item.get("type") == "listItem":
                    item_text = " ".join(
                        self._process_node(c) for c in item.get("content", [])
                    )
                    items.append(f"  - {item_text}")
            return "\n".join(items)
        elif node_type == "codeBlock":
            return f"```\n{self._extract_text_from_content(node.get('content', []))}\n```"

        return ""

    def _extract_text_from_content(self, content: List[Dict]) -> str:
        """Extract text from content nodes."""
        text_parts = []
        for node in content:
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))
        return "".join(text_parts)

    def _extract_acceptance_criteria(self, description: str) -> List[str]:
        """Extract acceptance criteria blocks from description."""
        if not description:
            return []

        # Common AC section markers
        ac_markers = [
            "acceptance criteria",
            "acceptance criterion",
            "ac:",
            "acs:",
            "criteria:",
        ]

        lines = description.split("\n")
        ac_blocks = []
        in_ac_section = False

        for line in lines:
            line_lower = line.lower().strip()

            # Check if we're entering an AC section
            if any(marker in line_lower for marker in ac_markers):
                in_ac_section = True
                continue

            # If in AC section, collect lines until we hit another header or empty line
            if in_ac_section:
                if line.strip() and not line.startswith("#"):
                    ac_blocks.append(line.strip())
                elif not line.strip():
                    in_ac_section = False

        return ac_blocks
