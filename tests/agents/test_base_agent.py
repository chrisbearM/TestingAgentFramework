"""
Unit tests for base_agent module

Tests cover:
1. Agent initialization
2. Abstract run() method enforcement
3. LLM calling with error handling
4. JSON response parsing (direct, markdown, fallback)
5. Error message formatting
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from ai_tester.agents.base_agent import BaseAgent


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock LLM client"""
    return Mock()


@pytest.fixture
def base_agent(mock_llm):
    """Create a BaseAgent instance for testing"""
    return BaseAgent(mock_llm)


# Create a concrete implementation for testing
class ConcreteAgent(BaseAgent):
    """Concrete agent for testing base functionality"""

    def run(self, context, **kwargs):
        """Implementation of abstract run method"""
        return {"status": "success"}, None


@pytest.fixture
def concrete_agent(mock_llm):
    """Create a concrete agent instance for testing"""
    return ConcreteAgent(mock_llm)


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestBaseAgentInitialization:
    """Tests for BaseAgent initialization"""

    def test_init_with_llm(self, mock_llm):
        """Test initialization with LLM client"""
        agent = BaseAgent(mock_llm)

        assert agent.llm is mock_llm
        assert agent.name == "BaseAgent"

    def test_init_concrete_agent_name(self, concrete_agent):
        """Test that concrete agent gets correct name"""
        assert concrete_agent.name == "ConcreteAgent"

    def test_init_stores_llm_reference(self, mock_llm):
        """Test that LLM reference is stored correctly"""
        agent = BaseAgent(mock_llm)

        # Should be the same object
        assert agent.llm is mock_llm


# ============================================================================
# RUN METHOD TESTS
# ============================================================================

class TestBaseAgentRun:
    """Tests for run method"""

    def test_run_not_implemented(self, base_agent):
        """Test that BaseAgent.run() raises NotImplementedError"""
        with pytest.raises(NotImplementedError) as exc_info:
            base_agent.run({})

        assert "BaseAgent must implement run()" in str(exc_info.value)

    def test_run_concrete_implementation(self, concrete_agent):
        """Test that concrete agent can implement run()"""
        result, error = concrete_agent.run({})

        assert result == {"status": "success"}
        assert error is None

    def test_run_with_context(self, concrete_agent):
        """Test that run receives context correctly"""
        context = {"key": "value"}
        result, error = concrete_agent.run(context)

        # Should not raise error
        assert error is None


# ============================================================================
# LLM CALL TESTS
# ============================================================================

class TestCallLLM:
    """Tests for _call_llm method"""

    def test_call_llm_success(self, concrete_agent, mock_llm):
        """Test successful LLM call"""
        mock_llm.complete_json.return_value = ('{"result": "success"}', None)

        result, error = concrete_agent._call_llm(
            "System prompt",
            "User prompt"
        )

        assert result == '{"result": "success"}'
        assert error is None
        mock_llm.complete_json.assert_called_once()

    def test_call_llm_with_custom_tokens(self, concrete_agent, mock_llm):
        """Test LLM call with custom max_tokens"""
        mock_llm.complete_json.return_value = ("response", None)

        concrete_agent._call_llm(
            "System prompt",
            "User prompt",
            max_tokens=4000
        )

        # Check that max_tokens was passed
        call_args = mock_llm.complete_json.call_args
        assert call_args[1]['max_tokens'] == 4000

    def test_call_llm_with_custom_model(self, concrete_agent, mock_llm):
        """Test LLM call with custom model"""
        mock_llm.complete_json.return_value = ("response", None)

        concrete_agent._call_llm(
            "System prompt",
            "User prompt",
            model="gpt-4o-mini"
        )

        # Check that model was passed
        call_args = mock_llm.complete_json.call_args
        assert call_args[1]['model'] == "gpt-4o-mini"

    def test_call_llm_with_error_from_llm(self, concrete_agent, mock_llm):
        """Test LLM call that returns an error"""
        mock_llm.complete_json.return_value = (None, "API Error")

        result, error = concrete_agent._call_llm(
            "System prompt",
            "User prompt"
        )

        assert result is None
        assert error == "API Error"

    def test_call_llm_with_exception(self, concrete_agent, mock_llm):
        """Test LLM call that raises an exception"""
        mock_llm.complete_json.side_effect = Exception("Connection failed")

        result, error = concrete_agent._call_llm(
            "System prompt",
            "User prompt"
        )

        assert result is None
        assert error is not None
        assert "ConcreteAgent LLM call failed" in error
        assert "Connection failed" in error

    def test_call_llm_default_parameters(self, concrete_agent, mock_llm):
        """Test that default parameters are used"""
        mock_llm.complete_json.return_value = ("response", None)

        concrete_agent._call_llm("System", "User")

        call_args = mock_llm.complete_json.call_args
        assert call_args[1]['max_tokens'] == 2000  # Default
        assert call_args[1]['model'] is None  # Default


# ============================================================================
# JSON PARSING TESTS
# ============================================================================

class TestParseJsonResponse:
    """Tests for _parse_json_response method"""

    def test_parse_valid_json(self, concrete_agent):
        """Test parsing valid JSON"""
        response = '{"key": "value", "number": 42}'
        result = concrete_agent._parse_json_response(response)

        assert result == {"key": "value", "number": 42}

    def test_parse_json_with_nested_objects(self, concrete_agent):
        """Test parsing nested JSON"""
        response = '{"outer": {"inner": "value"}, "list": [1, 2, 3]}'
        result = concrete_agent._parse_json_response(response)

        assert result["outer"]["inner"] == "value"
        assert result["list"] == [1, 2, 3]

    def test_parse_json_from_markdown_with_language(self, concrete_agent):
        """Test extracting JSON from markdown code block with language"""
        response = '''
Here is the result:
```json
{"status": "success"}
```
Hope that helps!
'''
        result = concrete_agent._parse_json_response(response)

        assert result == {"status": "success"}

    def test_parse_json_from_markdown_without_language(self, concrete_agent):
        """Test extracting JSON from markdown code block without language"""
        response = '''
```
{"extracted": true}
```
'''
        result = concrete_agent._parse_json_response(response)

        assert result == {"extracted": True}

    def test_parse_json_from_plain_text(self, concrete_agent):
        """Test extracting JSON from plain text response"""
        response = 'Some text before {"embedded": "json"} some text after'
        result = concrete_agent._parse_json_response(response)

        assert result == {"embedded": "json"}

    def test_parse_empty_string(self, concrete_agent):
        """Test parsing empty string"""
        result = concrete_agent._parse_json_response("")

        assert result == {}

    def test_parse_none(self, concrete_agent):
        """Test parsing None"""
        result = concrete_agent._parse_json_response(None)

        assert result == {}

    def test_parse_invalid_json(self, concrete_agent):
        """Test parsing invalid JSON returns empty dict"""
        response = "This is not JSON at all"
        result = concrete_agent._parse_json_response(response)

        assert result == {}

    def test_parse_malformed_json(self, concrete_agent):
        """Test parsing malformed JSON"""
        response = '{"key": "value", "incomplete"'
        result = concrete_agent._parse_json_response(response)

        assert result == {}

    def test_parse_json_with_special_characters(self, concrete_agent):
        """Test parsing JSON with special characters"""
        response = '{"text": "Line 1\\nLine 2", "quote": "He said \\"hello\\""}'
        result = concrete_agent._parse_json_response(response)

        assert result["text"] == "Line 1\nLine 2"
        assert result["quote"] == 'He said "hello"'

    def test_parse_json_array(self, concrete_agent):
        """Test parsing JSON array (wrapped in object)"""
        response = '{"items": [{"id": 1}, {"id": 2}]}'
        result = concrete_agent._parse_json_response(response)

        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == 1

    def test_parse_json_with_multiline_markdown(self, concrete_agent):
        """Test parsing multiline JSON in markdown"""
        response = '''
```json
{
  "key1": "value1",
  "key2": {
    "nested": "value2"
  }
}
```
'''
        result = concrete_agent._parse_json_response(response)

        assert result["key1"] == "value1"
        assert result["key2"]["nested"] == "value2"

    def test_parse_json_fallback_to_regex(self, concrete_agent):
        """Test that regex fallback works when direct parsing fails"""
        # This has text before JSON that would fail direct parsing
        response = 'The answer is: {"success": true} - hope this helps'
        result = concrete_agent._parse_json_response(response)

        assert result == {"success": True}


# ============================================================================
# ERROR FORMATTING TESTS
# ============================================================================

class TestFormatError:
    """Tests for _format_error method"""

    def test_format_error_adds_agent_name(self, concrete_agent):
        """Test that error formatting includes agent name"""
        error = concrete_agent._format_error("Something went wrong")

        assert error == "[ConcreteAgent] Something went wrong"

    def test_format_error_with_empty_string(self, concrete_agent):
        """Test formatting empty error message"""
        error = concrete_agent._format_error("")

        assert error == "[ConcreteAgent] "

    def test_format_error_preserves_message(self, concrete_agent):
        """Test that original error message is preserved"""
        original = "Connection timeout after 30 seconds"
        formatted = concrete_agent._format_error(original)

        assert original in formatted
        assert "[ConcreteAgent]" in formatted

    def test_format_error_with_multiline_message(self, concrete_agent):
        """Test formatting multiline error message"""
        error_msg = "Error occurred:\nLine 1\nLine 2"
        formatted = concrete_agent._format_error(error_msg)

        assert "[ConcreteAgent]" in formatted
        assert "Error occurred:" in formatted
        assert "Line 1" in formatted
        assert "Line 2" in formatted

    def test_format_error_different_agent_names(self, mock_llm):
        """Test that different agents show different names"""
        class AgentA(BaseAgent):
            def run(self, context, **kwargs):
                return None, None

        class AgentB(BaseAgent):
            def run(self, context, **kwargs):
                return None, None

        agent_a = AgentA(mock_llm)
        agent_b = AgentB(mock_llm)

        error_a = agent_a._format_error("Error")
        error_b = agent_b._format_error("Error")

        assert "[AgentA]" in error_a
        assert "[AgentB]" in error_b
        assert error_a != error_b


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestBaseAgentIntegration:
    """Integration tests combining multiple methods"""

    def test_call_llm_and_parse_json(self, concrete_agent, mock_llm):
        """Test calling LLM and parsing the JSON response"""
        mock_llm.complete_json.return_value = ('{"result": "success"}', None)

        # Call LLM
        response, error = concrete_agent._call_llm("System", "User")

        assert error is None

        # Parse response
        parsed = concrete_agent._parse_json_response(response)

        assert parsed == {"result": "success"}

    def test_call_llm_error_and_format(self, concrete_agent, mock_llm):
        """Test error handling flow from LLM call to formatting"""
        mock_llm.complete_json.side_effect = Exception("API Error")

        # Call LLM (will catch exception)
        result, error = concrete_agent._call_llm("System", "User")

        assert result is None
        assert "ConcreteAgent LLM call failed" in error

        # Format the error further if needed
        formatted = concrete_agent._format_error(error)

        assert "[ConcreteAgent]" in formatted

    def test_full_agent_workflow(self, mock_llm):
        """Test a complete agent workflow"""
        # Create custom agent
        class WorkflowAgent(BaseAgent):
            def run(self, context, **kwargs):
                # Call LLM
                response, error = self._call_llm(
                    "You are a helpful assistant",
                    f"Process: {context['data']}"
                )

                if error:
                    return None, self._format_error(error)

                # Parse response
                parsed = self._parse_json_response(response)

                return parsed, None

        mock_llm.complete_json.return_value = ('{"processed": true}', None)

        agent = WorkflowAgent(mock_llm)
        result, error = agent.run({"data": "test input"})

        assert error is None
        assert result == {"processed": True}
        mock_llm.complete_json.assert_called_once()
