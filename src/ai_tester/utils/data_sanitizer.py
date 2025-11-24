"""
Data Sanitizer - Security layer for protecting sensitive data before sending to LLMs

This module implements multiple sanitization strategies:
1. Field Whitelisting - Only allow safe Jira fields
2. Code Block Removal - Strip code blocks that may contain secrets
3. Image Security - Block images containing sensitive visual data
4. Entity Pseudonymization - Replace PII with semantic placeholders
5. PII Detection - Detect emails, IPs, phones, credit cards using Presidio

Phase 1 Implementation (Complete): Field Whitelisting + Code Block Removal
Phase 2.1 Implementation (Complete): Image Security (Complete Block)
Phase 2.2 Implementation (Complete): Entity Pseudonymization + PII Detection with Presidio
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
# PHASE 2.2: ENTITY PSEUDONYMIZATION & PII DETECTION
# ============================================================================

# Try to import Presidio (optional dependency)
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    AnalyzerEngine = None
    AnonymizerEngine = None


class EntityPseudonymizer:
    """
    Maintains bidirectional mapping between real entities and placeholders.

    Pseudonymization preserves semantic context while protecting PII:
    - Same entity always gets same placeholder (consistency)
    - Different entities get different placeholders
    - Preserves relationships and context for AI analysis

    Example:
        Input:  "Contact john@company.com at IP 10.0.45.23. Email john@company.com for access."
        Output: "Contact <EMAIL_1> at IP <IP_ADDRESS_1>. Email <EMAIL_1> for access."

    Security Note:
        - Mappings stored in memory only (never persisted to disk/logs)
        - Designed to be ephemeral (per-request lifecycle)
        - Reverse mapping available for debugging only
    """

    # Semantic type mapping for better AI understanding
    ENTITY_TYPE_MAPPING = {
        "EMAIL_ADDRESS": "EMAIL",
        "IP_ADDRESS": "IP_ADDRESS",
        "PHONE_NUMBER": "PHONE",
        "CREDIT_CARD": "CREDIT_CARD",
        "PERSON": "PERSON_NAME",
        "ORGANIZATION": "ORGANIZATION",
        "US_SSN": "SSN",
        "IBAN_CODE": "IBAN",
        "URL": "URL"
    }

    def __init__(self):
        """Initialize pseudonymizer with empty mappings"""
        # Forward mapping: real value → placeholder
        self.entity_to_placeholder: Dict[str, str] = {}

        # Reverse mapping: placeholder → real value (for audit/debugging only)
        self.placeholder_to_entity: Dict[str, str] = {}

        # Counters for each entity type
        self.counters: Dict[str, int] = {}

        # Security warning flag
        self._contains_sensitive_data = True

    def _get_next_placeholder(self, entity_type: str) -> str:
        """
        Generate next semantic placeholder for entity type.

        Args:
            entity_type: Presidio entity type (e.g., "EMAIL_ADDRESS")

        Returns:
            Semantic placeholder (e.g., "<EMAIL_1>")
        """
        # Map to semantic type
        semantic_type = self.ENTITY_TYPE_MAPPING.get(entity_type, entity_type)

        # Initialize counter if needed
        if semantic_type not in self.counters:
            self.counters[semantic_type] = 0

        # Increment and generate placeholder
        self.counters[semantic_type] += 1
        return f"<{semantic_type}_{self.counters[semantic_type]}>"

    def pseudonymize_entity(self, entity_value: str, entity_type: str) -> str:
        """
        Replace entity with consistent semantic placeholder.

        Same entity value always gets same placeholder (consistency).
        Different entity values get different placeholders.

        Args:
            entity_value: The actual sensitive value (e.g., "john@company.com")
            entity_type: Presidio entity type (e.g., "EMAIL_ADDRESS")

        Returns:
            Placeholder string (e.g., "<EMAIL_1>")
        """
        # Check if we've seen this entity before
        if entity_value in self.entity_to_placeholder:
            return self.entity_to_placeholder[entity_value]

        # Create new placeholder
        placeholder = self._get_next_placeholder(entity_type)

        # Store bidirectional mapping
        self.entity_to_placeholder[entity_value] = placeholder
        self.placeholder_to_entity[placeholder] = entity_value

        return placeholder

    def reverse_pseudonymization(self, text_with_placeholders: str) -> str:
        """
        Reverse pseudonymization for debugging/audit only.

        WARNING: Only use for internal debugging. Never send real data to LLMs.
        This defeats the entire purpose of pseudonymization if used in production.

        Args:
            text_with_placeholders: Text with placeholders like "<EMAIL_1>"

        Returns:
            Text with original sensitive values restored
        """
        result = text_with_placeholders
        for placeholder, entity in self.placeholder_to_entity.items():
            result = result.replace(placeholder, entity)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """
        Get safe audit summary (no sensitive mappings).

        Returns:
            Dictionary with entity counts by type
        """
        return {
            "total_entities": len(self.entity_to_placeholder),
            "by_type": self.counters.copy(),
            "note": "Entity mappings not included for security"
        }

    def __getstate__(self):
        """Prevent accidental pickling/serialization"""
        raise TypeError(
            "EntityPseudonymizer cannot be pickled or serialized. "
            "PII mappings must stay in memory only to prevent data leakage."
        )


def pseudonymize_text_with_presidio(
    text: str,
    pseudonymizer: EntityPseudonymizer,
    allowed_organizations: Optional[List[str]] = None,
    entities_to_detect: Optional[List[str]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Detect PII with Presidio and replace with semantic placeholders.

    Phase 2.2 Implementation: Conservative approach
    - Detects high-risk PII only (email, IP, phone, credit card)
    - Skips ORGANIZATION and PERSON to avoid false positives
    - Can be expanded with allow lists in future

    Args:
        text: Input text that may contain PII
        pseudonymizer: EntityPseudonymizer instance (maintains consistency)
        allowed_organizations: List of company names to whitelist (optional)
        entities_to_detect: Custom entity list (defaults to conservative set)

    Returns:
        Tuple of (pseudonymized_text, summary_dict)

    Example:
        >>> pseudonymizer = EntityPseudonymizer()
        >>> text = "Contact john@company.com at IP 10.0.45.23"
        >>> result, summary = pseudonymize_text_with_presidio(text, pseudonymizer)
        >>> print(result)
        "Contact <EMAIL_1> at IP <IP_ADDRESS_1>"
        >>> print(summary)
        {"entities_detected": 2, "by_type": {"EMAIL": 1, "IP_ADDRESS": 1}}
    """
    if not PRESIDIO_AVAILABLE:
        return text, {
            "error": "Presidio not installed",
            "note": "Run: pip install presidio-analyzer presidio-anonymizer"
        }

    if not text:
        return text, {"entities_detected": 0}

    try:
        # Initialize Presidio analyzer
        analyzer = AnalyzerEngine()

        # Conservative entity types (Phase 2.2 - avoid false positives)
        default_entities = [
            "EMAIL_ADDRESS",   # High risk
            "IP_ADDRESS",      # High risk
            "PHONE_NUMBER",    # High risk
            "CREDIT_CARD",     # High risk
            "IBAN_CODE",       # High risk (banking)
            "US_SSN",          # High risk (if applicable)
            # Note: URL detection removed - causes overlaps with email addresses
            # Skip: ORGANIZATION (too many false positives)
            # Skip: PERSON (names can be project code names, not always PII)
        ]

        entities = entities_to_detect or default_entities

        # Detect PII
        results = analyzer.analyze(
            text=text,
            entities=entities,
            language="en",
            allow_list=allowed_organizations or []
        )

        if not results:
            return text, {"entities_detected": 0}

        # Filter out overlapping detections (e.g., URL within EMAIL_ADDRESS)
        # Prioritize higher-confidence and longer matches
        filtered_results = []
        for result in results:
            overlaps = False
            for other in results:
                if result == other:
                    continue
                # Check if result overlaps with other
                if (result.start >= other.start and result.end <= other.end):
                    # result is contained within other - skip if other has higher score
                    if other.score >= result.score:
                        overlaps = True
                        break
            if not overlaps:
                filtered_results.append(result)

        # Sort by start position (reverse) to replace from end to start
        # This prevents offset issues when replacing
        results_sorted = sorted(filtered_results, key=lambda x: x.start, reverse=True)

        # Pseudonymize each entity
        pseudonymized = text
        for result in results_sorted:
            # Extract the actual entity value
            entity_value = text[result.start:result.end]

            # Get consistent placeholder
            placeholder = pseudonymizer.pseudonymize_entity(
                entity_value=entity_value,
                entity_type=result.entity_type
            )

            # Replace in text (from end to start to maintain offsets)
            pseudonymized = (
                pseudonymized[:result.start] +
                placeholder +
                pseudonymized[result.end:]
            )

        # Generate safe summary (no sensitive mappings)
        summary = {
            "entities_detected": len(filtered_results),
            "by_type": pseudonymizer.get_summary()["by_type"]
        }

        return pseudonymized, summary

    except Exception as e:
        # If Presidio fails, return original text and log error
        print(f"WARNING: Presidio pseudonymization failed: {e}")
        return text, {
            "error": str(e),
            "entities_detected": 0
        }


# ============================================================================
# PHASE 2.2: INTEGRATED SANITIZATION WITH PSEUDONYMIZATION
# ============================================================================

def sanitize_jira_ticket_with_pseudonymization(
    ticket: Dict[str, Any],
    whitelist_config: Optional[FieldWhitelistConfig] = None,
    remove_code: bool = True,
    detect_pii: bool = False,
    allowed_organizations: Optional[List[str]] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Comprehensive Jira ticket sanitization with optional PII pseudonymization.

    Combines all sanitization layers:
    - Phase 1: Field whitelisting + code block removal
    - Phase 2.2: PII detection + entity pseudonymization (opt-in)

    Args:
        ticket: Raw Jira ticket data
        whitelist_config: Field whitelist configuration (uses defaults if None)
        remove_code: Whether to remove code blocks from text fields
        detect_pii: Enable PII detection and pseudonymization (opt-in, default False)
        allowed_organizations: Company names to whitelist (won't be flagged as PII)

    Returns:
        Tuple of (sanitized_ticket, audit_summary)

    Example:
        >>> ticket = {
        ...     "key": "PROJ-123",
        ...     "fields": {
        ...         "description": "Contact john@company.com at IP 10.0.45.23"
        ...     }
        ... }
        >>> sanitized, audit = sanitize_jira_ticket_with_pseudonymization(
        ...     ticket, detect_pii=True
        ... )
        >>> print(sanitized['fields']['description'])
        "Contact <EMAIL_1> at IP <IP_ADDRESS_1>"
    """
    # Phase 1: Field whitelisting and code removal
    sanitized = sanitize_jira_ticket(ticket, whitelist_config, remove_code)

    # Initialize audit summary
    audit_summary = {
        "ticket_key": sanitized.get('key'),
        "pii_detection_enabled": detect_pii,
        "presidio_available": PRESIDIO_AVAILABLE
    }

    # Phase 2.2: PII detection and pseudonymization (opt-in)
    if detect_pii and PRESIDIO_AVAILABLE:
        # Initialize pseudonymizer (one per ticket for consistent mapping)
        pseudonymizer = EntityPseudonymizer()

        # Process description field
        description = sanitized.get('fields', {}).get('description', '')
        if description and isinstance(description, str):
            pseudonymized_desc, pii_summary = pseudonymize_text_with_presidio(
                text=description,
                pseudonymizer=pseudonymizer,
                allowed_organizations=allowed_organizations
            )
            sanitized['fields']['description'] = pseudonymized_desc

            # Add PII summary to audit
            audit_summary.update({
                "entities_replaced": pii_summary.get('entities_detected', 0),
                "entity_types": pii_summary.get('by_type', {}),
                "pii_detection_success": True
            })
        else:
            audit_summary["entities_replaced"] = 0

    elif detect_pii and not PRESIDIO_AVAILABLE:
        audit_summary.update({
            "error": "Presidio not installed",
            "note": "Run: pip install presidio-analyzer presidio-anonymizer",
            "entities_replaced": 0
        })
    else:
        audit_summary["entities_replaced"] = 0

    return sanitized, audit_summary


# Legacy functions for backward compatibility
def detect_pii(text: str) -> List[Dict[str, Any]]:
    """
    Legacy function - use pseudonymize_text_with_presidio instead.

    Detect PII in text using Presidio.

    Returns:
        List of detected PII entities with type and location
    """
    if not PRESIDIO_AVAILABLE:
        return []

    try:
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(
            text=text,
            entities=["EMAIL_ADDRESS", "IP_ADDRESS", "PHONE_NUMBER"],
            language="en"
        )
        return [
            {
                "type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score
            }
            for result in results
        ]
    except:
        return []


def redact_pii(text: str, pii_entities: List[Dict[str, Any]]) -> str:
    """
    Legacy function - use pseudonymize_text_with_presidio instead.

    Simple redaction (loses context). Pseudonymization is preferred.
    """
    result = text
    # Sort by start position (reverse) to maintain offsets
    sorted_entities = sorted(pii_entities, key=lambda x: x['start'], reverse=True)

    for entity in sorted_entities:
        result = result[:entity['start']] + "[REDACTED]" + result[entity['end']:]

    return result


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
