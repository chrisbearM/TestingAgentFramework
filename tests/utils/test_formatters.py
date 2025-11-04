"""Tests for formatting utilities"""
import pytest
from ai_tester.utils.formatters import slugify, safe_json_extract


class TestSlugify:
    """Tests for slugify function"""
    
    def test_basic_slugify(self):
        """Test basic text conversion"""
        assert slugify("Test Case") == "test-case"
    
    def test_slugify_with_numbers(self):
        """Test slugify with numbers"""
        assert slugify("Test Case 123") == "test-case-123"
    
    def test_slugify_removes_special_chars(self):
        """Test that special characters are removed"""
        assert slugify("Test@Case#123!") == "testcase123"
    
    def test_slugify_multiple_spaces(self):
        """Test that multiple spaces become single hyphen"""
        assert slugify("Test   Case") == "test-case"
    
    def test_slugify_empty_string(self):
        """Test with empty string"""
        assert slugify("") == ""
    
    def test_slugify_whitespace_only(self):
        """Test with whitespace only"""
        assert slugify("   ") == ""
    
    def test_slugify_with_hyphens(self):
        """Test that existing hyphens are preserved"""
        assert slugify("test-case") == "test-case"
    
    def test_slugify_unicode_removed(self):
        """Test that unicode characters are removed"""
        assert slugify("Test™ Case®") == "test-case"


class TestSafeJsonExtract:
    """Tests for safe_json_extract function"""
    
    def test_extract_plain_json(self):
        """Test extracting plain JSON"""
        result = safe_json_extract('{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_extract_json_with_markdown(self):
        """Test extracting JSON wrapped in markdown code blocks"""
        text = '```json\n{"key": "value"}\n```'
        result = safe_json_extract(text)
        assert result == {"key": "value"}
    
    def test_extract_json_without_json_marker(self):
        """Test extracting JSON in code blocks without 'json' marker"""
        text = '```\n{"key": "value"}\n```'
        result = safe_json_extract(text)
        assert result == {"key": "value"}
    
    def test_extract_json_from_mixed_text(self):
        """Test extracting JSON from text with other content"""
        text = 'Here is some JSON: {"key": "value"} and more text'
        result = safe_json_extract(text)
        assert result == {"key": "value"}
    
    def test_extract_nested_json(self):
        """Test extracting nested JSON"""
        text = '{"outer": {"inner": "value"}}'
        result = safe_json_extract(text)
        assert result == {"outer": {"inner": "value"}}
    
    def test_extract_json_with_arrays(self):
        """Test extracting JSON with arrays"""
        text = '{"items": [1, 2, 3]}'
        result = safe_json_extract(text)
        assert result == {"items": [1, 2, 3]}
    
    def test_empty_string_returns_none(self):
        """Test that empty string returns None"""
        assert safe_json_extract("") is None
    
    def test_invalid_json_returns_none(self):
        """Test that invalid JSON returns None"""
        assert safe_json_extract("not json at all") is None
    
    def test_none_input_returns_none(self):
        """Test that None input returns None"""
        assert safe_json_extract(None) is None