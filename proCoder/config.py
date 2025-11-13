import os
# from dotenv import load_dotenv
# import warnings

# Load variables from .env file in the current directory or parent directories
# dotenv_path = find_dotenv()
# if dotenv_path:
#     print(f"Loading environment variables from: {dotenv_path}")
#     load_dotenv(dotenv_path=dotenv_path)
# else:
#     warnings.warn(".env file not found. Please create one with your API key.", stacklevel=2)
#     # Allow loading from environment variables even if .env is missing
#     load_dotenv()

from dotenv import load_dotenv
import warnings
import os # Make sure os is imported
from pathlib import Path

# Attempt to load .env file from multiple locations
# 1. First check global config directory (~/.procoder/.env)
global_env = Path.home() / ".procoder" / ".env"
found_global = False
if global_env.exists():
    found_global = load_dotenv(dotenv_path=global_env)

# 2. Then check current directory and parent directories (project-specific)
found_local = load_dotenv()

# Use whichever was found (global takes precedence if both exist)
found_dotenv = found_global or found_local

# --- Required ---
# Don't raise error here - let individual commands check and provide helpful messages
API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Optional ---
# Default to a capable free model on OpenRouter if not set
MODEL_NAME = os.getenv("AI_MODEL_NAME", "google/gemini-flash-1.5-8b")
SITE_URL = os.getenv("YOUR_SITE_URL") # Optional header
SITE_NAME = os.getenv("YOUR_SITE_NAME") # Optional header

# --- Git ---
# Use helper to safely convert env var string to boolean
def get_bool_env(var_name, default=False):
    value = os.getenv(var_name, str(default)).lower()
    return value in ('true', '1', 't', 'y', 'yes')

GIT_AUTO_STAGE = get_bool_env("GIT_AUTO_STAGE", False)
GIT_AUTO_COMMIT = get_bool_env("GIT_AUTO_COMMIT", False)

# --- Other ---
# Max history messages (adjust as needed)
MAX_HISTORY_MESSAGES = 30
# Base context window approximation (conservative) - used for warnings
# Check your chosen model's actual limit on OpenRouter
APPROX_TOKEN_LIMIT = 8000 # Example for Gemini Flash 1.5


# Helper function to find .env up the directory tree
def find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=True):
    """
    Search in increasingly parent directories for the target file.
    Copied from python-dotenv find_dotenv function to avoid dependency or ensure it works standalone.
    """
    if usecwd or '__file__' not in globals():
        path = os.getcwd()
    else:
        path = os.path.dirname(os.path.abspath(__file__))

    for _ in range(100): # Limit search depth
        if os.path.exists(os.path.join(path, filename)):
            return os.path.join(path, filename)
        parent_path = os.path.abspath(os.path.join(path, os.pardir))
        if parent_path == path: # Reached root
            break
        path = parent_path

    if raise_error_if_not_found:
        raise IOError('File not found')

    return None # Return None if not found instead of raising error by default


# --- Helper Functions ---
def is_configured() -> bool:
    """Check if API key is configured."""
    return API_KEY is not None and len(API_KEY.strip()) > 0


def require_api_key():
    """
    Check if API key is configured, and provide helpful message if not.
    Returns True if configured, False otherwise.
    """
    if not is_configured():
        from rich.console import Console
        from rich.panel import Panel
        console = Console()

        console.print()
        console.print(Panel(
            "[bold yellow]⚠️  API Key Not Configured[/bold yellow]\n\n"
            "[cyan]proCoder needs an OpenRouter API key to function.[/cyan]\n\n"
            "[bold]Quick Setup:[/bold]\n"
            "  1. Run: [green]proCoder setup[/green]\n"
            "  2. Follow the interactive wizard (< 2 minutes)\n\n"
            "[bold]Or manually:[/bold]\n"
            "  1. Get a key from: [blue]https://openrouter.ai/keys[/blue]\n"
            "  2. Create a [yellow].env[/yellow] file with:\n"
            "     [dim]OPENROUTER_API_KEY=your_key_here[/dim]\n\n"
            "[dim]OpenRouter provides access to 100+ AI models including Claude, GPT-4, and Gemini.[/dim]",
            title="🔑 Configuration Required",
            border_style="yellow",
            padding=(1, 2)
        ))
        console.print()
        return False
    return True


# --- Print loaded config for verification (only if configured) ---
def print_config():
    """Print configuration status (only called when running commands)."""
    if is_configured():
        print("--- proCoder Configuration ---")
        print(f"Model: {MODEL_NAME}")
        print(f"API Key: Configured ✓")
        if SITE_URL: print(f"Site URL: {SITE_URL}")
        if SITE_NAME: print(f"Site Name: {SITE_NAME}")
        print(f"Auto Stage: {GIT_AUTO_STAGE}")
        print(f"Auto Commit: {GIT_AUTO_COMMIT}")
        print("-----------------------------")