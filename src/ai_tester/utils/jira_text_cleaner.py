"""
Utility functions for cleaning Jira text before sending to LLM.
Removes strikethrough content, out-of-scope items, and scope removal notes.
"""
import re
from typing import Set


def clean_jira_text_for_llm(text: str) -> str:
    """
    Clean Jira text to remove out-of-scope content before sending to LLM.
    Removes:
    - Strikethrough text (~~text~~)
    - Parenthetical scope removal notes AND the word/phrase before them
    - Lines that are marked as removed from scope
    - ANY operations/terms that are marked as removed ANYWHERE in the text

    Args:
        text: Raw text from Jira (description, acceptance criteria, etc.)

    Returns:
        Cleaned text with out-of-scope content removed
    """
    if not text:
        return text

    # Detect ANY words marked as removed (strikethrough or with removal notes)
    removed_terms: Set[str] = set()

    # Find strikethrough terms: ~~word~~
    strikethrough_matches = re.findall(r'~~(\w+)~~', text, re.IGNORECASE)
    removed_terms.update([term.lower() for term in strikethrough_matches])

    # Find words followed by removal notes: "word (removed from scope)"
    removal_note_matches = re.findall(
        r'\b(\w+)\s*\([^)]*(?:removed from scope|out of scope|not in scope|scope removed|deleted from scope)[^)]*\)',
        text,
        re.IGNORECASE
    )
    removed_terms.update([term.lower() for term in removal_note_matches])

    # Remove strikethrough text (Jira markdown: ~~text~~)
    text = re.sub(r'~{2,}[^~]+~{2,}', '', text)

    # Remove words/phrases followed by removal notes
    removal_phrases = [
        r'\b\w+\s*\([^)]*(?:removed from scope|out of scope|not in scope|scope removed|deleted from scope)[^)]*\)',
        r',?\s*and\s+\w+\s*\([^)]*(?:removed from scope|out of scope)[^)]*\)',
        r'\band\s+~~[^~]+~~',
    ]
    for pattern in removal_phrases:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove standalone parenthetical notes about removed scope
    removal_patterns = [
        r'\([^)]*removed from scope[^)]*\)',
        r'\([^)]*out of scope[^)]*\)',
        r'\([^)]*not in scope[^)]*\)',
        r'\([^)]*scope removed[^)]*\)',
        r'\([^)]*deleted from scope[^)]*\)',
        r'\([^)]*operation removed from scope[^)]*\)',
    ]
    for pattern in removal_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # For each removed term, remove ALL occurrences throughout the text
    for term in removed_terms:
        if not term:
            continue

        # Remove from comma-separated lists: "create, update, and delete" -> "create and update"
        text = re.sub(rf',?\s+and\s+{term}\b', '', text, flags=re.IGNORECASE)
        text = re.sub(rf'\b{term},?\s+and\s+', '', text, flags=re.IGNORECASE)

        # Remove from slash-separated lists: "Create/Update/Delete" -> "Create/Update"
        text = re.sub(rf'/{term}(?=/|\)|\s|,|$)', '', text, flags=re.IGNORECASE)
        text = re.sub(rf'{term}/(?=\w)', '', text, flags=re.IGNORECASE)

        # Remove standalone occurrences with "operations": "delete operations" -> "operations"
        text = re.sub(rf'\b{term}\s+operations?\b', 'operations', text, flags=re.IGNORECASE)

    # Remove lines that contain removal indicators
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line_lower = line.lower()
        # Skip lines that are mostly strikethrough or contain removal notes
        if (line.strip().startswith('~~') or
            'removed from scope' in line_lower or
            'out of scope' in line_lower or
            'not in scope' in line_lower):
            continue
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # Clean up artifacts
    text = re.sub(r'\s*,\s*,\s*', ', ', text)  # Double commas
    text = re.sub(r'\s+and\s+and\s+', ' and ', text)  # Double "and"
    text = re.sub(r',\s*and\s+', ' and ', text)  # ", and" -> " and"
    text = re.sub(r'\(\s*\)', '', text)  # Empty parentheses
    text = re.sub(r'\s+operations', ' operations', text)  # Extra space before operations
    text = re.sub(r'/\s*/', '/', text)  # Clean up double slashes
    text = re.sub(r'(^|[^/])/$', r'\1', text)  # Remove trailing slash

    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple blank lines
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces
    text = re.sub(r'\.\s*\.', '.', text)  # Double periods
    text = text.strip()

    return text
