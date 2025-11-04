"""String formatting utilities"""
import re


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: The text to convert
        
    Returns:
        A slugified version of the text
        
    Example:
        >>> slugify("Test Case 123")
        'test-case-123'
        
        >>> slugify("Hello World!")
        'hello-world'
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.strip().lower()
    
    # Remove special characters
    text = re.sub(r"[^a-z0-9\-\s]", "", text)
    
    # Replace spaces with hyphens
    text = re.sub(r"\s+", "-", text)
    
    # Remove multiple hyphens
    text = re.sub(r"-+", "-", text)
    
    return text


def safe_json_extract(text: str) -> dict:
    """
    Extract JSON from text that might contain markdown or other formatting.
    
    Args:
        text: Text that contains JSON (possibly with markdown code blocks)
        
    Returns:
        Extracted JSON as dictionary, or None if no valid JSON found
        
    Example:
        >>> safe_json_extract('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
    """
    import json
    
    if not text:
        return None
    
    # Remove markdown code blocks
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text, flags=re.IGNORECASE)
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try to find JSON object in text
    match = re.search(r"(\{(?:.|\n)*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass
    
    return None