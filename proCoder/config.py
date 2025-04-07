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

# Attempt to load .env file. load_dotenv handles finding it.
# Returns True if a .env file was found and loaded, False otherwise.
found_dotenv = load_dotenv()

if not found_dotenv:
    warnings.warn(
        ".env file not found in current directory or parent directories. "
        "Loading environment variables from OS environment.",
        stacklevel=2
    )
    # Note: load_dotenv() already attempted to load from the environment if .env wasn't found,
    # so we don't strictly need to call it again here.

# (Rest of your config.py continues below, like API_KEY = os.getenv(...))

# --- Required ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY not found in environment variables or .env file. "
        "Get one from https://openrouter.ai/keys"
    )

# --- Optional ---
# Default to a capable free model on OpenRouter if not set
MODEL_NAME = os.getenv("AI_MODEL_NAME", "google/gemini-flash-1.5")
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


# --- Print loaded config for verification ---
print("--- proCoder Configuration ---")
print(f"Model: {MODEL_NAME}")
print(f"API Key Loaded: {'Yes' if API_KEY else 'NO (ERROR!)'}")
if SITE_URL: print(f"Site URL Header: {SITE_URL}")
if SITE_NAME: print(f"Site Name Header: {SITE_NAME}")
print(f"Auto Stage: {GIT_AUTO_STAGE}")
print(f"Auto Commit: {GIT_AUTO_COMMIT}")
print("-----------------------------")