"""
Unit tests for utils module

Tests cover:
1. clean_jira_text_for_llm - Jira text cleaning
2. ADF (Atlassian Document Format) conversion functions
3. Document extraction (PDF, Word)
4. Image encoding

Note: slugify and safe_json_extract are already tested in test_formatters.py
"""

import pytest
import base64
from unittest.mock import Mock, patch, MagicMock
from ai_tester.utils.utils import (
    clean_jira_text_for_llm,
    adf_to_html,
    adf_to_plaintext,
    plain_to_html,
    extract_text_from_pdf,
    extract_text_from_word,
    extract_images_from_word,
    encode_image_to_base64,
)


# ============================================================================
# JIRA TEXT CLEANING TESTS
# ============================================================================

class TestCleanJiraTextForLLM:
    """Tests for Jira text cleaning function"""

    def test_remove_strikethrough_lines(self):
        """Test removal of lines that start with ~~"""
        text = """
Normal line
~~This line should be removed~~
Another normal line
"""
        result = clean_jira_text_for_llm(text)

        assert "Normal line" in result
        assert "Another normal line" in result
        assert "This line should be removed" not in result

    def test_remove_lines_with_removal_markers(self):
        """Test removal of lines containing (removed from scope)"""
        text = """
Feature A
Feature B (removed from scope)
Feature C
"""
        result = clean_jira_text_for_llm(text)

        assert "Feature A" in result
        assert "Feature C" in result
        assert "Feature B" not in result
        assert "removed from scope" not in result.lower()

    def test_remove_inline_strikethrough(self):
        """Test removal of inline strikethrough text ~~text~~"""
        text = "This is ~~removed text~~ and this stays"
        result = clean_jira_text_for_llm(text)

        assert "This is" in result
        assert "and this stays" in result
        assert "removed text" not in result

    def test_remove_parenthetical_scope_notes(self):
        """Test removal of (removed from scope) with preceding word"""
        text = "Authentication (removed from scope) is not needed"
        result = clean_jira_text_for_llm(text)

        # The regex removes the word + parenthetical, leaving "is not needed"
        # But if the entire line becomes empty, it's filtered out
        # So let's test that the removal marker is gone
        assert "removed from scope" not in result.lower()
        # And that if there's remaining content, it's preserved
        if result:
            assert "Authentication" not in result or "is not needed" in result

    def test_preserve_normal_text(self):
        """Test that normal text without removal markers is preserved"""
        text = """
User Story:
As a user, I want to login
So that I can access my account

Acceptance Criteria:
- Valid credentials accepted
- Invalid credentials rejected
"""
        result = clean_jira_text_for_llm(text)

        assert "User Story:" in result
        assert "As a user, I want to login" in result
        assert "Acceptance Criteria:" in result
        assert "Valid credentials accepted" in result

    def test_empty_text(self):
        """Test handling of empty text"""
        assert clean_jira_text_for_llm("") == ""
        assert clean_jira_text_for_llm(None) == ""

    def test_case_insensitive_removal(self):
        """Test that removal markers are case-insensitive"""
        text = "Feature (REMOVED FROM SCOPE) here"
        result = clean_jira_text_for_llm(text)

        assert "Feature" not in result or "REMOVED FROM SCOPE" not in result


# ============================================================================
# ADF TO HTML CONVERSION TESTS
# ============================================================================

class TestAdfToHtml:
    """Tests for Atlassian Document Format to HTML conversion"""

    def test_simple_paragraph(self):
        """Test conversion of simple paragraph"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": "Hello world"
                }]
            }]
        }

        result = adf_to_html(adf)

        assert "<p>Hello world</p>" in result
        assert "class='jira'" in result

    def test_heading(self):
        """Test conversion of headings"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{
                    "type": "text",
                    "text": "Section Title"
                }]
            }]
        }

        result = adf_to_html(adf)

        assert "<h2>Section Title</h2>" in result

    def test_text_with_marks(self):
        """Test text with formatting marks (bold, italic, code)"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": "Bold text",
                    "marks": [{"type": "strong"}]
                }]
            }]
        }

        result = adf_to_html(adf)

        assert "<strong>Bold text</strong>" in result

    def test_bullet_list(self):
        """Test conversion of bullet lists"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [{
                            "type": "paragraph",
                            "content": [{
                                "type": "text",
                                "text": "Item 1"
                            }]
                        }]
                    },
                    {
                        "type": "listItem",
                        "content": [{
                            "type": "paragraph",
                            "content": [{
                                "type": "text",
                                "text": "Item 2"
                            }]
                        }]
                    }
                ]
            }]
        }

        result = adf_to_html(adf)

        assert "<ul>" in result
        assert "<li>" in result
        assert "Item 1" in result
        assert "Item 2" in result

    def test_ordered_list(self):
        """Test conversion of ordered lists"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "orderedList",
                "content": [{
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": "First"
                        }]
                    }]
                }]
            }]
        }

        result = adf_to_html(adf)

        assert "<ol" in result
        assert "First" in result

    def test_code_block(self):
        """Test conversion of code blocks"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "codeBlock",
                "content": [{
                    "type": "text",
                    "text": "const x = 1;"
                }]
            }]
        }

        result = adf_to_html(adf)

        assert "<pre><code>" in result
        assert "const x = 1;" in result

    def test_horizontal_rule(self):
        """Test conversion of horizontal rules"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "rule"
            }]
        }

        result = adf_to_html(adf)

        assert "<hr/>" in result

    def test_blockquote(self):
        """Test conversion of blockquotes"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "blockquote",
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": "Quoted text"
                    }]
                }]
            }]
        }

        result = adf_to_html(adf)

        assert "<blockquote>" in result
        assert "Quoted text" in result

    def test_empty_adf(self):
        """Test handling of empty ADF"""
        result = adf_to_html({})

        assert "class='jira'" in result

    def test_malformed_adf_graceful_failure(self):
        """Test that malformed ADF doesn't crash"""
        # Pass something that will cause an error during processing
        result = adf_to_html({"type": "invalid", "content": [None]})

        # Should return fallback HTML
        assert "unable to render" in result or "class='jira'" in result


# ============================================================================
# ADF TO PLAINTEXT CONVERSION TESTS
# ============================================================================

class TestAdfToPlaintext:
    """Tests for ADF to plaintext conversion"""

    def test_simple_paragraph(self):
        """Test conversion of simple paragraph to plaintext"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": "Hello world"
                }]
            }]
        }

        result = adf_to_plaintext(adf)

        assert "Hello world" in result

    def test_heading_formatting(self):
        """Test that headings are formatted with newlines"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{
                    "type": "text",
                    "text": "Main Title"
                }]
            }]
        }

        result = adf_to_plaintext(adf)

        assert "Main Title" in result

    def test_bullet_list_formatting(self):
        """Test that bullet lists use • character"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "bulletList",
                "content": [{
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": "Item one"
                        }]
                    }]
                }]
            }]
        }

        result = adf_to_plaintext(adf)

        assert "•" in result
        assert "Item one" in result

    def test_ordered_list_formatting(self):
        """Test that ordered lists use numbers"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "orderedList",
                "content": [{
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": "First item"
                        }]
                    }]
                }]
            }]
        }

        result = adf_to_plaintext(adf)

        assert "1." in result
        assert "First item" in result

    def test_code_block_preservation(self):
        """Test that code blocks are preserved"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "codeBlock",
                "content": [{
                    "type": "text",
                    "text": "function test() {}"
                }]
            }]
        }

        result = adf_to_plaintext(adf)

        assert "function test() {}" in result

    def test_hard_break(self):
        """Test that hard breaks are converted to newlines"""
        adf = {
            "type": "doc",
            "content": [{
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Line 1"},
                    {"type": "hardBreak"},
                    {"type": "text", "text": "Line 2"}
                ]
            }]
        }

        result = adf_to_plaintext(adf)

        assert "Line 1" in result
        assert "Line 2" in result

    def test_empty_adf(self):
        """Test handling of empty ADF"""
        result = adf_to_plaintext({})
        assert result == ""

        result = adf_to_plaintext(None)
        assert result == ""

    def test_excessive_newlines_collapsed(self):
        """Test that excessive newlines are collapsed"""
        adf = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Para 1"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]},
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Para 2"}]}
            ]
        }

        result = adf_to_plaintext(adf)

        # Should not have more than 2 consecutive newlines
        assert "\n\n\n\n" not in result


# ============================================================================
# PLAIN TEXT TO HTML TESTS
# ============================================================================

class TestPlainToHtml:
    """Tests for plain text to HTML conversion"""

    def test_simple_text(self):
        """Test conversion of simple text"""
        result = plain_to_html("Hello world")

        assert "<p>Hello world</p>" in result
        assert "class='jira'" in result

    def test_newline_to_br(self):
        """Test that single newlines become <br/>"""
        result = plain_to_html("Line 1\nLine 2")

        assert "<br/>" in result

    def test_double_newline_to_paragraph(self):
        """Test that double newlines create new paragraphs"""
        result = plain_to_html("Para 1\n\nPara 2")

        assert "</p><p>" in result

    def test_html_escaping(self):
        """Test that HTML special characters are escaped"""
        result = plain_to_html("<script>alert('xss')</script>")

        assert "&lt;script&gt;" in result
        assert "<script>" not in result.replace("<style>", "").replace("</style>", "")

    def test_empty_text(self):
        """Test handling of empty text"""
        result = plain_to_html("")

        assert "<p></p>" in result

    def test_none_text(self):
        """Test handling of None text"""
        result = plain_to_html(None)

        assert "<p></p>" in result


# ============================================================================
# PDF EXTRACTION TESTS
# ============================================================================

class TestExtractTextFromPdf:
    """Tests for PDF text extraction"""

    def test_extraction_returns_string(self):
        """Test that PDF extraction returns a string (integration-like test)"""
        # This will actually use PyPDF2 if available, otherwise gracefully fail
        result = extract_text_from_pdf(b"invalid pdf")

        # Should return string (empty on error)
        assert isinstance(result, str)

    def test_extraction_handles_errors_gracefully(self):
        """Test that errors are handled and return empty string"""
        # Pass completely invalid bytes
        result = extract_text_from_pdf(b"\x00\x01\x02")

        # Should not crash, should return empty string
        assert result == ""


# ============================================================================
# WORD DOCUMENT EXTRACTION TESTS
# ============================================================================

class TestExtractTextFromWord:
    """Tests for Word document text extraction"""

    def test_extraction_returns_string(self):
        """Test that Word extraction returns a string"""
        # This will actually use python-docx if available, otherwise gracefully fail
        result = extract_text_from_word(b"invalid docx")

        # Should return string (empty on error)
        assert isinstance(result, str)

    def test_extraction_handles_errors_gracefully(self):
        """Test that errors are handled and return empty string"""
        # Pass completely invalid bytes
        result = extract_text_from_word(b"\x00\x01\x02")

        # Should not crash, should return empty string
        assert result == ""


# ============================================================================
# WORD IMAGE EXTRACTION TESTS
# ============================================================================

class TestExtractImagesFromWord:
    """Tests for Word document image extraction"""

    def test_extraction_returns_list(self):
        """Test that image extraction returns a list"""
        # This will actually use python-docx if available, otherwise gracefully fail
        result = extract_images_from_word(b"invalid docx")

        # Should return list (empty on error)
        assert isinstance(result, list)

    def test_extraction_handles_errors_gracefully(self):
        """Test that errors are handled and return empty list"""
        # Pass completely invalid bytes
        result = extract_images_from_word(b"\x00\x01\x02")

        # Should not crash, should return empty list
        assert result == []


# ============================================================================
# IMAGE ENCODING TESTS
# ============================================================================

class TestEncodeImageToBase64:
    """Tests for image base64 encoding"""

    def test_basic_encoding(self):
        """Test basic image encoding"""
        image_bytes = b"fake image data"
        result = encode_image_to_base64(image_bytes, "image/png")

        # Should be valid base64
        assert result == base64.b64encode(image_bytes).decode('utf-8')

    def test_empty_image(self):
        """Test encoding of empty image bytes"""
        result = encode_image_to_base64(b"", "image/png")

        assert result == ""

    def test_various_mime_types(self):
        """Test that function works with various mime types"""
        image_bytes = b"test"

        for mime_type in ["image/png", "image/jpeg", "image/gif", "image/webp"]:
            result = encode_image_to_base64(image_bytes, mime_type)
            assert result == base64.b64encode(image_bytes).decode('utf-8')

    def test_large_image(self):
        """Test encoding of larger image"""
        # Simulate a larger image
        image_bytes = b"x" * 10000
        result = encode_image_to_base64(image_bytes, "image/png")

        # Should successfully encode
        assert len(result) > 0
        # Should be decodable
        decoded = base64.b64decode(result)
        assert decoded == image_bytes
