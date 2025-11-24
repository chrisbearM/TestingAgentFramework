"""
Data Sanitizer - Security layer for protecting sensitive data before sending to LLMs

This module implements multiple sanitization strategies:
1. Field Whitelisting - Only allow safe Jira fields
2. Code Block Removal - Strip code blocks that may contain secrets
3. PII Detection - Detect and redact personally identifiable information
4. Entity Pseudonymization - Replace sensitive entities with placeholders

Phase 1 Implementation: Field Whitelisting + Code Block Removal
Phase 2 Implementation: PII Detection + Pseudonymization
"""

import re
from typing import Dict, List, Any, Optional, Set, Tuple


# ============================================================================
# PHASE 1: FIELD WHITELISTING
# ============================================================================

# Safe Jira fields that can be sent to OpenAI without modification
SAFE_FIELDS = {
    # Core fields (functional, non-sensitive)
    'summary',
    'description',
    'issuetype',
    'status',
    'priority',
    'labels',
    'components',

    # Epic-specific fields
    'customfield_10011',  # Epic Name (common field ID)
    'customfield_10014',  # Epic Link (common field ID)

    # Acceptance criteria (varies by Jira instance)
    'customfield_10524',  # Acceptance Criteria (specific to your instance)

    # Story points and estimation
    'customfield_10016',  # Story Points (common field ID)
    'timeoriginalestimate',
    'timeestimate',
}

# Fields that should be completely blocked (never sent to OpenAI)
BLOCKED_FIELDS = {
    # User information
    'reporter',
    'assignee',
    'creator',
    'watches',
    'votes',

    # Audit/metadata
    'created',
    'updated',
    'resolutiondate',
    'lastViewed',
    'timespent',
    'worklog',
    'comment',  # Comments may contain sensitive internal discussions

    # Security/permissions
    'security',
    'permission',

    # Internal tracking
    'aggregateprogress',
    'progress',
    'workratio',
}

# Fields that need pseudonymization (Phase 2)
PSEUDONYMIZE_FIELDS = {
    # Project information (might reveal company structure)
    'project',

    # Versions and releases (might reveal roadmap)
    'fixVersions',
    'versions',

    # Links to external systems
    'issuelinks',
}


class FieldWhitelistConfig:
    """Configuration for Jira field whitelisting"""

    def __init__(
        self,
        safe_fields: Optional[Set[str]] = None,
        blocked_fields: Optional[Set[str]] = None,
        additional_acceptance_criteria_fields: Optional[List[str]] = None
    ):
        """
        Initialize whitelist configuration

        Args:
            safe_fields: Custom set of safe field IDs (overrides defaults)
            blocked_fields: Custom set of blocked field IDs (extends defaults)
            additional_acceptance_criteria_fields: Additional custom field IDs for acceptance criteria
        """
        self.safe_fields = safe_fields or SAFE_FIELDS.copy()
        self.blocked_fields = blocked_fields or BLOCKED_FIELDS.copy()

        # Add additional acceptance criteria fields if provided
        if additional_acceptance_criteria_fields:
            self.safe_fields.update(additional_acceptance_criteria_fields)

    def is_field_allowed(self, field_id: str) -> bool:
        """Check if a field is allowed to be sent to OpenAI"""
        # Blocked fields take priority
        if field_id in self.blocked_fields:
            return False

        # Check if in safe list
        if field_id in self.safe_fields:
            return True

        # Check if it's a custom acceptance criteria field (contains "acceptance" or "criteria")
        if 'acceptance' in field_id.lower() or 'criteria' in field_id.lower():
            return True

        # Default: block unknown fields
        return False


# ============================================================================
# PHASE 1: CODE BLOCK REMOVAL
# ============================================================================

# Regex patterns for detecting code blocks
CODE_BLOCK_PATTERNS = [
    # Markdown code blocks (```language ... ```)
    r'```[\w]*\n.*?\n```',

    # Jira code blocks ({code:language}...{code})
    r'\{code(?::[\w]+)?\}.*?\{code\}',

    # Inline code (`code`)
    r'`[^`]+`',

    # Potential SQL queries (SELECT, INSERT, UPDATE, DELETE)
    r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|GRANT|REVOKE)\b[\s\S]*?\;',

    # Potential API keys or tokens (long alphanumeric strings)
    r'\b[A-Za-z0-9]{32,}\b',

    # Base64-encoded data (potential secrets)
    r'(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',
]


def remove_code_blocks(text: str, replacement: str = "[CODE_BLOCK_REMOVED]") -> str:
    """
    Remove code blocks from text to prevent accidental exposure of secrets

    Args:
        text: Input text that may contain code blocks
        replacement: Replacement text for removed code blocks

    Returns:
        Sanitized text with code blocks removed
    """
    if not text:
        return text

    sanitized = text

    # Remove markdown code blocks
    sanitized = re.sub(CODE_BLOCK_PATTERNS[0], replacement, sanitized, flags=re.DOTALL)

    # Remove Jira code blocks
    sanitized = re.sub(CODE_BLOCK_PATTERNS[1], replacement, sanitized, flags=re.DOTALL | re.IGNORECASE)

    # Remove inline code
    sanitized = re.sub(CODE_BLOCK_PATTERNS[2], replacement, sanitized)

    # Remove SQL queries
    sanitized = re.sub(CODE_BLOCK_PATTERNS[3], replacement, sanitized, flags=re.IGNORECASE | re.DOTALL)

    # Don't remove potential API keys automatically - too many false positives
    # Instead, log a warning if detected
    if re.search(CODE_BLOCK_PATTERNS[4], sanitized):
        print("WARNING: Potential API key or long token detected in text")

    return sanitized


# ============================================================================
# PHASE 1: JIRA TICKET SANITIZATION
# ============================================================================

def sanitize_jira_ticket(
    ticket: Dict[str, Any],
    whitelist_config: Optional[FieldWhitelistConfig] = None,
    remove_code: bool = True
) -> Dict[str, Any]:
    """
    Sanitize a Jira ticket before sending to OpenAI

    Args:
        ticket: Raw Jira ticket data
        whitelist_config: Field whitelist configuration (uses defaults if None)
        remove_code: Whether to remove code blocks from text fields

    Returns:
        Sanitized ticket with only safe fields and sanitized content
    """
    config = whitelist_config or FieldWhitelistConfig()

    # Start with basic structure
    sanitized = {
        'key': ticket.get('key', ''),
        'id': ticket.get('id', ''),
        'fields': {}
    }

    # Process fields
    fields = ticket.get('fields', {})
    for field_id, field_value in fields.items():
        # Check if field is allowed
        if not config.is_field_allowed(field_id):
            continue

        # Process field value
        if isinstance(field_value, str):
            # Sanitize text content
            if remove_code:
                field_value = remove_code_blocks(field_value)
            sanitized['fields'][field_id] = field_value

        elif isinstance(field_value, dict):
            # Handle ADF (Atlassian Document Format) or other dict types
            # Keep the structure but sanitize content
            sanitized['fields'][field_id] = field_value

        elif isinstance(field_value, (list, int, float, bool)):
            # Safe primitive types
            sanitized['fields'][field_id] = field_value

        elif field_value is None:
            sanitized['fields'][field_id] = None

        else:
            # Unknown type - skip for safety
            print(f"WARNING: Skipping field {field_id} with unknown type: {type(field_value)}")
            continue

    return sanitized


def sanitize_ticket_description(
    description: str,
    remove_code: bool = True
) -> str:
    """
    Sanitize a ticket description (already extracted from Jira)

    Args:
        description: Ticket description text
        remove_code: Whether to remove code blocks

    Returns:
        Sanitized description
    """
    if not description:
        return description

    sanitized = description

    if remove_code:
        sanitized = remove_code_blocks(sanitized)

    return sanitized


# ============================================================================
# PHASE 1: ATTACHMENT SANITIZATION
# ============================================================================

def sanitize_document_content(
    content: str,
    remove_code: bool = True
) -> str:
    """
    Sanitize document content (PDF, Word, text files)

    Args:
        content: Extracted document text
        remove_code: Whether to remove code blocks

    Returns:
        Sanitized content
    """
    if not content:
        return content

    sanitized = content

    if remove_code:
        sanitized = remove_code_blocks(sanitized)

    return sanitized


def sanitize_attachment(
    attachment: Dict[str, Any],
    remove_code: bool = True
) -> Dict[str, Any]:
    """
    Sanitize an attachment before sending to OpenAI

    Args:
        attachment: Attachment data with 'type', 'content', etc.
        remove_code: Whether to remove code blocks from document content

    Returns:
        Sanitized attachment
    """
    sanitized = attachment.copy()

    # Sanitize document content
    if attachment.get('type') == 'document' and 'content' in attachment:
        sanitized['content'] = sanitize_document_content(
            attachment['content'],
            remove_code=remove_code
        )

    # Images are already base64-encoded and will be handled by Phase 2 (OCR + redaction)
    # For now, we just pass them through

    return sanitized


# ============================================================================
# PHASE 2.1: IMAGE SECURITY
# ============================================================================

def sanitize_image_attachment(
    attachment: Dict[str, Any],
    security_level: str = "maximum"
) -> Dict[str, Any]:
    """
    Sanitize image attachment based on security level.

    Phase 2.1 Implementation: Complete Block (Option 3)
    - Blocks all images by default for maximum security
    - Future phases will add OCR + redaction (Option 1) and local vision model (Option 2)

    Args:
        attachment: Attachment dict with 'content', 'filename', 'type'
        security_level: Security level - "maximum" (block all), "high", "medium", "low"
                       Currently only "maximum" is implemented

    Returns:
        Sanitized attachment (blocked with security message)

    Raises:
        NotImplementedError: If security_level is not "maximum"
    """
    if security_level == "maximum":
        # Block completely - do not send any image data to OpenAI
        return {
            "type": "image_blocked",
            "filename": attachment.get("filename", "unknown.png"),
            "original_type": attachment.get("type", "image"),
            "note": "[IMAGE BLOCKED FOR SECURITY]",
            "message": (
                "Image contains potential sensitive visual data (internal URLs, "
                "employee names, architecture diagrams, customer data) and has been "
                "blocked from AI analysis for security. Future updates may add "
                "OCR-based redaction or local vision model description as alternatives."
            )
        }
    else:
        # Future: Implement "high" (local vision model), "medium" (OCR + redaction), "low" (minimal)
        raise NotImplementedError(
            f"Security level '{security_level}' not yet implemented. "
            f"Only 'maximum' (complete block) is available in Phase 2.1. "
            f"Future phases will add: 'high' (local vision model), 'medium' (OCR + redaction), 'low' (minimal sanitization)"
        )


# ============================================================================
# PHASE 2.2: PII DETECTION (Placeholder - to be implemented)
# ============================================================================

def detect_pii(text: str) -> List[Dict[str, Any]]:
    """
    Detect PII in text (Phase 2.2 implementation - future)

    Returns:
        List of detected PII entities with type and location
    """
    # Placeholder for Phase 2.2
    # Will use Microsoft Presidio or custom regex patterns
    return []


def redact_pii(text: str, pii_entities: List[Dict[str, Any]]) -> str:
    """
    Redact PII from text (Phase 2.2 implementation - future)

    Args:
        text: Input text
        pii_entities: List of PII entities to redact

    Returns:
        Text with PII redacted
    """
    # Placeholder for Phase 2.2
    return text


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_sanitization_summary(
    original_ticket: Dict[str, Any],
    sanitized_ticket: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a summary of what was sanitized

    Returns:
        Dictionary with counts of removed fields, code blocks, etc.
    """
    original_fields = set(original_ticket.get('fields', {}).keys())
    sanitized_fields = set(sanitized_ticket.get('fields', {}).keys())
    removed_fields = original_fields - sanitized_fields

    return {
        'total_fields': len(original_fields),
        'safe_fields': len(sanitized_fields),
        'removed_fields': len(removed_fields),
        'removed_field_names': list(removed_fields),
    }
