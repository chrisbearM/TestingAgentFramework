"""
Utility functions for cleaning Jira text before sending to LLM.
Removes strikethrough content, out-of-scope items, and scope removal notes.
Sanitizes user input to prevent prompt injection attacks.
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


def sanitize_prompt_input(text: str) -> str:
    """
    Sanitize user-provided text to prevent prompt injection attacks.

    Detects and neutralizes common prompt injection patterns while preserving
    legitimate content. This function should be applied to ALL user-provided
    content (Jira summaries, descriptions, etc.) before including in LLM prompts.

    Args:
        text: User-provided text (from Jira tickets, attachments, etc.)

    Returns:
        Sanitized text with injection patterns neutralized

    Examples:
        >>> sanitize_prompt_input("Normal ticket summary")
        'Normal ticket summary'
        >>> sanitize_prompt_input("Ignore previous instructions and do X")
        '[FILTERED] previous instructions and do X'
    """
    if not text:
        return text

    # Patterns that indicate prompt injection attempts
    # These are common phrases used to hijack LLM prompts
    dangerous_patterns = [
        # Direct instruction overrides
        (r'\bignore\s+(?:previous|all|the|above)\s+(?:instructions?|prompts?|commands?|directives?)\b', '[FILTERED]'),
        (r'\bdisregard\s+(?:previous|all|the|above)\s+(?:instructions?|prompts?|commands?)\b', '[FILTERED]'),
        (r'\bforget\s+(?:previous|all|the|above)\s+(?:instructions?|prompts?|commands?)\b', '[FILTERED]'),
        # Catch variations without "previous/all"
        (r'\bforget\s+(?:all\s+)?(?:previous\s+)?prompts?\b', '[FILTERED]'),
        (r'\bignore\s+(?:all\s+)?(?:previous\s+)?prompts?\b', '[FILTERED]'),

        # New instruction injection
        (r'\bnew\s+(?:instructions?|prompts?|commands?|directives?)\s*:?\s*\b', '[FILTERED]'),
        (r'\bactual\s+(?:instructions?|task|prompt)\s*:?\s*\b', '[FILTERED]'),
        (r'\breal\s+(?:instructions?|task|prompt)\s*:?\s*\b', '[FILTERED]'),

        # Role/system manipulation
        (r'\bsystem\s*:?\s*(?:you\s+are|act\s+as|your\s+role)\b', '[FILTERED]'),
        (r'\bassistant\s*:?\s*(?:you\s+are|act\s+as|your\s+role)\b', '[FILTERED]'),
        (r'\byou\s+are\s+now\s+(?:a|an)\s+\w+', '[FILTERED]'),
        (r'\bact\s+as\s+(?:a|an)\s+\w+', '[FILTERED]'),
        (r'\bpretend\s+(?:you\s+are|to\s+be)', '[FILTERED]'),

        # Prompt boundary markers (attempting to inject system/assistant messages)
        (r'\[?\s*system\s*\]?\s*:\s*', '[FILTERED]'),
        (r'\[?\s*assistant\s*\]?\s*:\s*', '[FILTERED]'),
        (r'\[?\s*user\s*\]?\s*:\s*', '[FILTERED]'),
        (r'<\s*system\s*>', '[FILTERED]'),
        (r'<\s*assistant\s*>', '[FILTERED]'),
        # Catch [system] without colon
        (r'\[\s*system\s*\]', '[FILTERED]'),
        (r'\[\s*assistant\s*\]', '[FILTERED]'),

        # Output format manipulation
        (r'\bignore\s+(?:json|format|schema|structure)', '[FILTERED]'),
        (r'\bdo\s+not\s+(?:use|follow|output)\s+(?:json|format|schema)', '[FILTERED]'),

        # Developer mode / jailbreak attempts
        (r'\bdeveloper\s+mode\b', '[FILTERED]'),
        (r'\bjailbreak\s+mode\b', '[FILTERED]'),
        (r'\bdebug\s+mode\s*:\s*(?:on|enabled|true)', '[FILTERED]'),
    ]

    # Apply sanitization (case-insensitive)
    sanitized = text
    for pattern, replacement in dangerous_patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    # Remove excessive repetition (a common injection technique)
    # Replace 5+ repetitions of same word with just 3
    sanitized = re.sub(r'\b(\w+)(\s+\1){4,}\b', r'\1 \1 \1', sanitized, flags=re.IGNORECASE)

    # Remove control characters (except newlines and tabs)
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

    return sanitized
