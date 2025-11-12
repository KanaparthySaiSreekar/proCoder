"""
Token counting utilities using tiktoken for accurate context management.
"""
import json
from typing import List, Dict, Optional
from rich.console import Console

console = Console()

# Try to import tiktoken, but make it optional
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    console.print("[yellow]Warning: tiktoken not installed. Token counting will be approximate.[/yellow]")
    console.print("[yellow]Install with: pip install tiktoken[/yellow]")


def get_encoding_for_model(model_name: str):
    """Get the appropriate tiktoken encoding for a model."""
    if not TIKTOKEN_AVAILABLE:
        return None

    try:
        # Try to get encoding for specific model
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fall back to cl100k_base for unknown models (used by GPT-4, GPT-3.5-turbo)
        console.print(f"[dim]Unknown model '{model_name}', using cl100k_base encoding[/dim]")
        return tiktoken.get_encoding("cl100k_base")


def count_tokens_for_messages(messages: List[Dict[str, str]], model_name: str = "gpt-4") -> int:
    """
    Count tokens in a list of messages using the proper encoding for the model.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model_name: Name of the model to get encoding for

    Returns:
        Number of tokens in the messages
    """
    if not TIKTOKEN_AVAILABLE:
        # Approximate token count (rough estimate: 1 token ≈ 4 characters)
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        return total_chars // 4

    encoding = get_encoding_for_model(model_name)
    if encoding is None:
        # Fall back to character-based estimation
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        return total_chars // 4

    # Count tokens properly
    num_tokens = 0

    # Different models have different token overhead per message
    tokens_per_message = 3  # For GPT-3.5-turbo and GPT-4
    tokens_per_name = 1

    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if value:
                num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 3  # Every reply is primed with assistant
    return num_tokens


def count_tokens_for_text(text: str, model_name: str = "gpt-4") -> int:
    """
    Count tokens in a text string.

    Args:
        text: The text to count tokens for
        model_name: Name of the model to get encoding for

    Returns:
        Number of tokens in the text
    """
    if not TIKTOKEN_AVAILABLE:
        # Approximate: 1 token ≈ 4 characters
        return len(text) // 4

    encoding = get_encoding_for_model(model_name)
    if encoding is None:
        return len(text) // 4

    return len(encoding.encode(text))


def truncate_messages_to_limit(
    messages: List[Dict[str, str]],
    token_limit: int,
    model_name: str = "gpt-4",
    preserve_system: bool = True
) -> tuple[List[Dict[str, str]], int]:
    """
    Truncate messages to fit within a token limit while preserving important context.

    Args:
        messages: List of message dictionaries
        token_limit: Maximum number of tokens
        model_name: Name of the model for token counting
        preserve_system: Whether to always keep system messages

    Returns:
        Tuple of (truncated_messages, removed_count)
    """
    current_tokens = count_tokens_for_messages(messages, model_name)

    if current_tokens <= token_limit:
        return messages, 0

    # Separate system messages from conversation
    system_messages = [msg for msg in messages if msg.get('role') == 'system']
    conversation_messages = [msg for msg in messages if msg.get('role') != 'system']

    # Always keep system messages if preserve_system is True
    if preserve_system:
        system_tokens = count_tokens_for_messages(system_messages, model_name)
        available_tokens = token_limit - system_tokens
    else:
        system_messages = []
        available_tokens = token_limit

    # Keep as many recent conversation messages as possible
    truncated_conversation = []
    tokens_used = 0

    for msg in reversed(conversation_messages):
        msg_tokens = count_tokens_for_messages([msg], model_name)
        if tokens_used + msg_tokens <= available_tokens:
            truncated_conversation.insert(0, msg)
            tokens_used += msg_tokens
        else:
            break

    removed_count = len(conversation_messages) - len(truncated_conversation)
    result = system_messages + truncated_conversation

    if removed_count > 0:
        console.print(f"[yellow]Truncated {removed_count} old messages to fit token limit[/yellow]")

    return result, removed_count


def estimate_context_window(model_name: str) -> int:
    """
    Estimate the context window size for a given model.

    Args:
        model_name: Name of the model

    Returns:
        Estimated context window size in tokens
    """
    model_lower = model_name.lower()

    # Common model context windows
    if "gpt-4-32k" in model_lower:
        return 32768
    elif "gpt-4" in model_lower or "claude-3" in model_lower:
        return 8192
    elif "gpt-3.5-turbo-16k" in model_lower:
        return 16384
    elif "gpt-3.5" in model_lower:
        return 4096
    elif "gemini" in model_lower:
        if "1.5" in model_lower:
            return 1000000  # Gemini 1.5 has huge context
        return 32768
    elif "claude-2" in model_lower:
        return 100000
    elif "llama" in model_lower:
        return 4096
    else:
        # Conservative default
        return 4096


def get_safe_token_limit(model_name: str, safety_margin: float = 0.8) -> int:
    """
    Get a safe token limit that leaves room for the response.

    Args:
        model_name: Name of the model
        safety_margin: Percentage of context window to use for input (default 0.8 = 80%)

    Returns:
        Safe token limit for input
    """
    context_window = estimate_context_window(model_name)
    return int(context_window * safety_margin)


def format_token_info(token_count: int, model_name: str) -> str:
    """
    Format token count information with context window percentage.

    Args:
        token_count: Current token count
        model_name: Name of the model

    Returns:
        Formatted string with token information
    """
    context_window = estimate_context_window(model_name)
    percentage = (token_count / context_window) * 100

    color = "green" if percentage < 50 else "yellow" if percentage < 80 else "red"

    return f"[{color}]{token_count:,} tokens ({percentage:.1f}% of {context_window:,})[/{color}]"
