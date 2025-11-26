"""
Base Agent Class
Provides common functionality for all agents in the multi-agent system
"""

from typing import Tuple, Optional, Dict, Any
import json
import re


class BaseAgent:
    """Base class for all agents in the multi-agent system"""

    def __init__(self, llm):
        """
        Initialize the agent with an LLM client

        Args:
            llm: LLMClient instance for making API calls
        """
        self.llm = llm
        self.name = self.__class__.__name__

    def run(self, context: Dict[str, Any], **kwargs) -> Tuple[Any, Optional[str]]:
        """
        Main execution method - must be implemented by subclasses

        Args:
            context: Dictionary containing all necessary context for the agent
            **kwargs: Additional keyword arguments

        Returns:
            Tuple of (result, error) where error is None on success
        """
        raise NotImplementedError(f"{self.name} must implement run()")

    def _call_llm(self, system_prompt: str, user_prompt: str,
                  max_tokens: int = 2000, model: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Standard LLM call with error handling

        Args:
            system_prompt: System prompt defining the agent's role
            user_prompt: User prompt with specific task details
            max_tokens: Maximum tokens for the response
            model: Optional model override (e.g., 'gpt-4o-mini' for cheaper extraction tasks)

        Returns:
            Tuple of (result, error) where error is None on success
        """
        try:
            result, error = self.llm.complete_json(
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
                model=model
            )
            return result, error
        except Exception as e:
            return None, f"{self.name} LLM call failed: {str(e)}"

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response with robust error handling

        Args:
            response: Raw string response from LLM

        Returns:
            Parsed JSON dictionary, or empty dict if parsing fails
        """
        if not response:
            return {}

        try:
            # Try direct JSON parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try to find any JSON object in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            # If all else fails, return empty dict
            return {}

    def _format_error(self, error_msg: str) -> str:
        """
        Format error message with agent name

        Args:
            error_msg: Raw error message

        Returns:
            Formatted error message
        """
        return f"[{self.name}] {error_msg}"

    @staticmethod
    def get_accuracy_principles() -> str:
        """
        Get universal accuracy principles that should be included in all agent prompts.
        This prevents hallucination and filler content across all agents.

        Returns:
            String containing accuracy principles to append to system prompts
        """
        return """

CRITICAL - ACCURACY OVER COMPLETENESS:
⚠️ Information accuracy is PARAMOUNT - never fabricate content to fill space!
- If there is insufficient information to provide a complete answer, state what's missing explicitly
- If a section has no relevant content, write "None" or "Not applicable" rather than inventing plausible details
- Do NOT make up technical details, test scenarios, requirements, or any other content that isn't evident from the input
- Do NOT pad responses to meet an expected length or token count
- Do NOT carry over information from previous requests - each request is completely independent
- An honest "insufficient information" or "None" is infinitely more valuable than a plausible-sounding fabrication
- Quality and accuracy trump quantity - a short, accurate response is better than a long, speculative one

EXAMPLES OF CORRECT BEHAVIOR:
✓ Good: "Out of Scope: None specified in original ticket"
✗ Bad: "Out of Scope: Real-time updates, Mobile app, Admin dashboard" (invented items)

✓ Good: "Testing Notes: Test sync with 2000 vehicle records from Element API"
✗ Bad: "Testing Notes: Test all CRUD operations, verify API responses, check error handling" (generic filler)

✓ Good: "Technical Notes: Unable to determine implementation approach without architecture details"
✗ Bad: "Technical Notes: Use microservices, implement caching, add monitoring" (fabricated specifics)"""
