"""
Token management utilities for LLM context window management.

Provides token counting, estimation, and smart truncation to prevent
exceeding model context limits.
"""
import tiktoken
from typing import Dict, Any, Tuple


# Model context limits (tokens)
MODEL_LIMITS = {
    "gpt-4o": 128000,
    "gpt-4o-2024-08-06": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-3.5-turbo": 16385,
}

# Reserve tokens for response (output)
DEFAULT_RESPONSE_RESERVE = 4000  # Reserve 4k tokens for model response


def get_encoding_for_model(model: str) -> tiktoken.Encoding:
    """
    Get the tiktoken encoding for a specific model.

    Args:
        model: Model name (e.g., "gpt-4o", "gpt-4o-mini")

    Returns:
        tiktoken.Encoding object for the model

    Raises:
        ValueError: If model is not supported
    """
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for newer models
        print(f"Warning: Model '{model}' not found in tiktoken, using cl100k_base encoding")
        return tiktoken.get_encoding("cl100k_base")


def estimate_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Estimate the number of tokens in a text string.

    Args:
        text: Text to estimate tokens for
        model: Model name to use for encoding

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    enc = get_encoding_for_model(model)
    return len(enc.encode(text))


def estimate_messages_tokens(messages: list, model: str = "gpt-4o") -> int:
    """
    Estimate tokens for a list of chat messages.

    Based on OpenAI's token counting for chat models:
    - Every message has overhead: <|start|>{role/name}\n{content}<|end|>\n
    - Every reply is primed with <|start|>assistant<|message|>

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name to use for encoding

    Returns:
        Estimated token count
    """
    enc = get_encoding_for_model(model)

    # Tokens per message overhead (role, separators, etc.)
    tokens_per_message = 3
    tokens_per_name = 1  # If name field is present

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if value:
                num_tokens += len(enc.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name

    # Every reply is primed with assistant
    num_tokens += 3

    return num_tokens


def get_max_tokens_for_model(model: str) -> int:
    """
    Get the maximum context window size for a model.

    Args:
        model: Model name

    Returns:
        Maximum token count, or 128000 as default for unknown models
    """
    # Extract base model name (remove version suffixes)
    base_model = model.split("-20")[0]  # Handle models like gpt-4o-2024-08-06

    return MODEL_LIMITS.get(base_model, MODEL_LIMITS.get(model, 128000))


def check_token_limit(
    text: str,
    model: str = "gpt-4o",
    max_tokens: int = None,
    response_reserve: int = DEFAULT_RESPONSE_RESERVE
) -> Tuple[bool, int, int]:
    """
    Check if text fits within model's context window.

    Args:
        text: Text to check
        model: Model name
        max_tokens: Override default model limit
        response_reserve: Tokens to reserve for response

    Returns:
        Tuple of (fits_within_limit, current_tokens, max_allowed_tokens)
    """
    if max_tokens is None:
        max_tokens = get_max_tokens_for_model(model)

    # Subtract response reserve from limit
    max_allowed = max_tokens - response_reserve

    current_tokens = estimate_tokens(text, model)

    return (current_tokens <= max_allowed, current_tokens, max_allowed)


def truncate_to_token_limit(
    text: str,
    max_tokens: int,
    model: str = "gpt-4o",
    truncation_strategy: str = "end",
    preserve_structure: bool = True
) -> str:
    """
    Truncate text to fit within token limit using smart strategies.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed
        model: Model name for encoding
        truncation_strategy: Where to truncate ("end", "start", "middle")
        preserve_structure: Try to preserve complete sentences/paragraphs

    Returns:
        Truncated text that fits within token limit
    """
    if not text:
        return text

    enc = get_encoding_for_model(model)
    tokens = enc.encode(text)

    # If already within limit, return as-is
    if len(tokens) <= max_tokens:
        return text

    # Truncate tokens based on strategy
    if truncation_strategy == "end":
        truncated_tokens = tokens[:max_tokens]
    elif truncation_strategy == "start":
        truncated_tokens = tokens[-max_tokens:]
    elif truncation_strategy == "middle":
        # Keep first and last portions
        keep_each = max_tokens // 2
        truncated_tokens = tokens[:keep_each] + tokens[-keep_each:]
    else:
        raise ValueError(f"Unknown truncation strategy: {truncation_strategy}")

    # Decode back to text
    truncated_text = enc.decode(truncated_tokens)

    # Try to preserve structure if requested
    if preserve_structure and truncation_strategy == "end":
        # Try to end at a sentence boundary
        last_period = truncated_text.rfind('.')
        last_newline = truncated_text.rfind('\n\n')

        # Use paragraph break if available, otherwise sentence break
        cutoff = max(last_newline, last_period)
        if cutoff > len(truncated_text) * 0.8:  # Only if we don't lose too much
            truncated_text = truncated_text[:cutoff + 1]

    return truncated_text


def split_text_to_chunks(
    text: str,
    chunk_size: int,
    model: str = "gpt-4o",
    overlap: int = 100
) -> list:
    """
    Split text into chunks of approximately chunk_size tokens with overlap.

    Useful for processing long documents that exceed context limits.

    Args:
        text: Text to split
        chunk_size: Target size of each chunk in tokens
        model: Model name for encoding
        overlap: Number of tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text:
        return []

    enc = get_encoding_for_model(model)
    tokens = enc.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))

        # Move start forward, with overlap
        start = end - overlap if end < len(tokens) else end

    return chunks


def validate_prompt_size(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o",
    response_reserve: int = DEFAULT_RESPONSE_RESERVE
) -> Dict[str, Any]:
    """
    Validate that system + user prompts fit within model limits.

    Args:
        system_prompt: System message content
        user_prompt: User message content
        model: Model name
        response_reserve: Tokens to reserve for response

    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "total_tokens": int,
            "max_allowed": int,
            "system_tokens": int,
            "user_tokens": int,
            "exceeds_by": int (if invalid)
        }
    """
    system_tokens = estimate_tokens(system_prompt, model)
    user_tokens = estimate_tokens(user_prompt, model)

    # Add message overhead (approximately 10 tokens per message)
    overhead = 20
    total_tokens = system_tokens + user_tokens + overhead

    max_allowed = get_max_tokens_for_model(model) - response_reserve

    result = {
        "valid": total_tokens <= max_allowed,
        "total_tokens": total_tokens,
        "max_allowed": max_allowed,
        "system_tokens": system_tokens,
        "user_tokens": user_tokens,
    }

    if not result["valid"]:
        result["exceeds_by"] = total_tokens - max_allowed

    return result
