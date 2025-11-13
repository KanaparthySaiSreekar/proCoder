import time
import base64
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from openai import OpenAI, APIError, RateLimitError, AuthenticationError, BadRequestError
from . import config
from . import token_counter
from rich.console import Console

console = Console()

# Global client instance (lazy initialization)
_client = None

def get_client():
    """Get or create the OpenAI client instance."""
    global _client
    if _client is None:
        if not config.API_KEY:
            raise ValueError("API key not configured. Run 'proCoder setup' first.")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.API_KEY,
        )
    return _client

# Prepare optional headers
extra_headers = {}
if config.SITE_URL:
    extra_headers["HTTP-Referer"] = config.SITE_URL
if config.SITE_NAME:
    extra_headers["X-Title"] = config.SITE_NAME

def prepare_prompt_for_api(history: list[dict], loaded_files: dict[str, str], last_user_message: str) -> list[dict]:
    """
    Formats the history and potentially adds relevant file context
    to the last user message for the API call.
    """
    # Basic approach: Identify filenames mentioned in the last user message
    mentioned_files = []
    for filename in loaded_files:
        # Simple check if filename appears in the message
        if filename in last_user_message or filename.split('/')[-1] in last_user_message:
             mentioned_files.append(filename)

    context_to_add = ""
    if mentioned_files:
        context_to_add += "Relevant file context:\n\n"
        for filename in mentioned_files:
            context_to_add += f"--- {filename} ---\n```\n{loaded_files[filename]}\n```\n\n"
        context_to_add += "---\nUser Query:\n"

    # Prepare the history for the API
    api_history = []
    system_prompt_content = ""

    # Combine system prompts
    for msg in history:
        if msg['role'] == 'system':
            system_prompt_content += msg['content'] + "\n\n"
        else:
             # Ensure roles are 'user' or 'assistant' (OpenAI standard, OpenRouter uses this via OpenAI lib)
             role = msg['role'] if msg['role'] in ['user', 'assistant', 'model'] else 'user'
             # Remap 'model' to 'assistant' for OpenAI API format
             if role == 'model':
                  role = 'assistant'

             # Add context to the *last* user message content if files were mentioned
             content = msg['content']
             if msg['role'] == 'user' and msg['content'] == last_user_message and context_to_add:
                  content = context_to_add + content

             api_history.append({'role': role, 'content': content})

    # Prepend combined system prompt if any exists
    if system_prompt_content:
         api_history.insert(0, {'role': 'system', 'content': system_prompt_content.strip()})

    # Token counting and context management
    token_count = token_counter.count_tokens_for_messages(api_history, model_name=config.MODEL_NAME)
    safe_limit = token_counter.get_safe_token_limit(config.MODEL_NAME)

    # Display token usage
    token_info = token_counter.format_token_info(token_count, config.MODEL_NAME)
    console.print(f"[dim]Context size: {token_info}[/dim]")

    # Warn if approaching limit
    if token_count > safe_limit:
        console.print(f"[bold red]Warning: Token count ({token_count:,}) exceeds safe limit ({safe_limit:,})[/bold red]")
        console.print("[yellow]Consider using /clear to start a fresh conversation or loading fewer files.[/yellow]")

        # Auto-truncate if severely over limit
        context_window = token_counter.estimate_context_window(config.MODEL_NAME)
        if token_count > context_window * 0.95:
            console.print("[bold red]Context severely over limit. Auto-truncating conversation history...[/bold red]")
            api_history, removed = token_counter.truncate_messages_to_limit(
                api_history,
                safe_limit,
                config.MODEL_NAME,
                preserve_system=True
            )
            console.print(f"[yellow]Removed {removed} old messages to fit within limit[/yellow]")

    return api_history


def stream_ai_response(prompt_history: list[dict], model_name: str):
    """
    Calls the OpenRouter API with streaming enabled and yields content chunks.
    Handles common API errors.
    """
    retry_attempts = 3
    delay = 2 # seconds

    for attempt in range(retry_attempts):
        try:
            stream = get_client().chat.completions.create(
                model=model_name,
                messages=prompt_history,
                stream=True,
                extra_headers=extra_headers if extra_headers else None,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return # Signal successful completion of stream

        except AuthenticationError as e:
            console.print(f"[bold red]API Error: Authentication failed. Check your OPENROUTER_API_KEY.[/bold red]")
            console.print(f"Details: {e}")
            raise  # Don't retry auth errors
        except RateLimitError as e:
            console.print(f"[bold yellow]API Error: Rate limit exceeded. Retrying in {delay}s... ({attempt + 1}/{retry_attempts})[/bold yellow]")
            console.print(f"Details: {e}")
            time.sleep(delay)
            delay *= 2 # Exponential backoff
        except BadRequestError as e:
            console.print(f"[bold red]API Error: Bad request. Often due to invalid model name or prompt format.[/bold red]")
            console.print(f"Model used: {model_name}")
            console.print(f"Details: {e}")
            # Consider printing the prompt history here for debugging (potentially large)
            # import json; print(json.dumps(prompt_history, indent=2))
            raise # Don't retry bad requests usually
        except APIError as e:
            console.print(f"[bold red]API Error: An unexpected API error occurred. Retrying in {delay}s... ({attempt + 1}/{retry_attempts})[/bold red]")
            console.print(f"Details: {e}")
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            console.print(f"[bold red]Error during API call: {type(e).__name__}. Retrying in {delay}s... ({attempt + 1}/{retry_attempts})[/bold red]")
            console.print(f"Details: {e}")
            time.sleep(delay)
            delay *= 2

    # If all retries fail
    console.print("[bold red]API call failed after multiple retries.[/bold red]")
    raise APIError("API call failed after multiple retries.") # Raise generic API error


def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    Encode an image file to base64.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string or None if error
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        console.print(f"[red]Error encoding image:[/red] {e}")
        return None


def get_image_mime_type(image_path: str) -> str:
    """
    Get the MIME type of an image file.

    Args:
        image_path: Path to the image file

    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    return mime_type or "image/jpeg"


def create_image_message_content(image_paths: List[str], text: str = "") -> List[Dict[str, Any]]:
    """
    Create message content with both text and images.

    Args:
        image_paths: List of paths to image files
        text: Text content to include

    Returns:
        List of content items for multimodal message
    """
    content = []

    # Add text if provided
    if text:
        content.append({
            "type": "text",
            "text": text
        })

    # Add each image
    for image_path in image_paths:
        base64_image = encode_image_to_base64(image_path)
        if base64_image:
            mime_type = get_image_mime_type(image_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })
            console.print(f"[green]Added image:[/green] {Path(image_path).name}")

    return content


def add_images_to_message(message: Dict[str, Any], image_paths: List[str]) -> Dict[str, Any]:
    """
    Add images to an existing message.

    Args:
        message: Message dictionary
        image_paths: List of image file paths

    Returns:
        Updated message with images
    """
    if not image_paths:
        return message

    # Convert simple string content to multimodal content
    if isinstance(message.get("content"), str):
        text_content = message["content"]
        message["content"] = create_image_message_content(image_paths, text_content)
    elif isinstance(message.get("content"), list):
        # Already multimodal, append images
        for image_path in image_paths:
            base64_image = encode_image_to_base64(image_path)
            if base64_image:
                mime_type = get_image_mime_type(image_path)
                message["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                })
                console.print(f"[green]Added image:[/green] {Path(image_path).name}")

    return message


def validate_images(image_paths: List[str]) -> List[str]:
    """
    Validate that image paths exist and are supported formats.

    Args:
        image_paths: List of image file paths

    Returns:
        List of valid image paths
    """
    supported_formats = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    valid_paths = []

    for image_path in image_paths:
        path = Path(image_path)

        if not path.exists():
            console.print(f"[yellow]Image not found:[/yellow] {image_path}")
            continue

        if path.suffix.lower() not in supported_formats:
            console.print(f"[yellow]Unsupported image format:[/yellow] {image_path}")
            console.print(f"[dim]Supported: {', '.join(supported_formats)}[/dim]")
            continue

        # Check file size (warn if > 20MB)
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 20:
            console.print(f"[yellow]Warning: Large image ({size_mb:.1f}MB):[/yellow] {image_path}")
            console.print("[dim]This may increase API costs[/dim]")

        valid_paths.append(image_path)

    return valid_paths