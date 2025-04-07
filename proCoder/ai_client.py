import time
from openai import OpenAI, APIError, RateLimitError, AuthenticationError, BadRequestError
from . import config
from rich.console import Console

console = Console()

# Initialize the client once
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=config.API_KEY,
)

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

    # TODO: Add token counting here and potentially truncate history or context if needed
    # import tiktoken
    # enc = tiktoken.encoding_for_model("gpt-4") # Use appropriate encoder
    # token_count = len(enc.encode(json.dumps(api_history))) # Rough estimate
    # if token_count > config.APPROX_TOKEN_LIMIT:
    #     console.print(f"[yellow]Warning: Estimated prompt token count ({token_count}) may exceed limit ({config.APPROX_TOKEN_LIMIT}). Truncating history may be needed.[/yellow]")

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
            stream = client.chat.completions.create(
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