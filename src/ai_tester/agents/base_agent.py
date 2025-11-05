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
                  max_tokens: int = 2000) -> Tuple[Optional[str], Optional[str]]:
        """
        Standard LLM call with error handling

        Args:
            system_prompt: System prompt defining the agent's role
            user_prompt: User prompt with specific task details
            max_tokens: Maximum tokens for the response

        Returns:
            Tuple of (result, error) where error is None on success
        """
        try:
            result, error = self.llm.complete_json(
                system_prompt,
                user_prompt,
                max_tokens=max_tokens
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
