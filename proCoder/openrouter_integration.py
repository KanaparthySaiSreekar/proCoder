"""
OpenRouter integration utilities for seamless authentication and model management.
"""
import os
import json
import webbrowser
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align
import requests

from . import ascii_art

console = Console()

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_AUTH_URL = "https://openrouter.ai/keys"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


class OpenRouterClient:
    """Manages OpenRouter API interactions and authentication."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.models_cache: Optional[List[Dict]] = None
        self.usage_cache: Optional[Dict] = None

    def validate_api_key(self) -> bool:
        """Validate the API key by making a test request."""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{OPENROUTER_API_BASE}/auth/key",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            console.print(f"[red]Error validating API key:[/red] {e}")
            return False

    def get_account_info(self) -> Optional[Dict]:
        """Get account information including credits and usage."""
        if not self.api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{OPENROUTER_API_BASE}/auth/key",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            console.print(f"[red]Error fetching account info:[/red] {e}")
            return None

    def fetch_available_models(self, force_refresh: bool = False) -> List[Dict]:
        """Fetch available models from OpenRouter."""
        if self.models_cache and not force_refresh:
            return self.models_cache

        try:
            response = requests.get(OPENROUTER_MODELS_URL, timeout=15)
            if response.status_code == 200:
                data = response.json()
                self.models_cache = data.get("data", [])
                return self.models_cache
            return []
        except Exception as e:
            console.print(f"[red]Error fetching models:[/red] {e}")
            return []

    def display_model_browser(self, category: Optional[str] = None):
        """Display an interactive model browser."""
        models = self.fetch_available_models()

        if not models:
            console.print("[yellow]Could not fetch models from OpenRouter.[/yellow]")
            return

        # Filter by category if specified
        if category:
            category_lower = category.lower()
            models = [m for m in models if category_lower in m.get("id", "").lower()]

        # Header
        header_panel = Panel(
            f"[bold bright_cyan]Browsing {len(models)} AI Models[/bold bright_cyan]\n"
            f"{ascii_art.BRAIN} Choose from multiple providers and capabilities",
            title=f"[bold magenta]{ascii_art.ROCKET} Model Browser[/bold magenta]",
            border_style="bright_magenta",
            padding=(0, 2)
        )
        console.print(header_panel)
        console.print()

        # Create categorized view
        categories = {}
        for model in models:
            model_id = model.get("id", "")
            provider = model_id.split("/")[0] if "/" in model_id else "other"
            if provider not in categories:
                categories[provider] = []
            categories[provider].append(model)

        # Color scheme for different providers
        provider_colors = {
            "anthropic": "bright_magenta",
            "openai": "bright_green",
            "google": "bright_blue",
            "meta-llama": "bright_yellow",
            "mistralai": "bright_cyan",
            "deepseek": "bright_red",
        }

        # Display by category
        for provider, provider_models in sorted(categories.items()):
            provider_color = provider_colors.get(provider, "bright_white")
            console.print(f"\n[bold {provider_color}]{ascii_art.LIGHTNING} {provider.upper()} Models ({len(provider_models)})[/bold {provider_color}]")

            table = Table(show_header=True, header_style="bold magenta", border_style=provider_color)
            table.add_column("Model ID", style="cyan", width=40)
            table.add_column("Context", justify="right", style="bright_yellow")
            table.add_column("Pricing", justify="right", style="bright_green")
            table.add_column("Description", width=50, style="white")

            for model in sorted(provider_models, key=lambda x: x.get("id", "")):
                model_id = model.get("id", "N/A")
                context = model.get("context_length", "N/A")
                if context != "N/A":
                    context = f"{int(context):,}" if isinstance(context, (int, float)) else str(context)

                pricing = model.get("pricing", {})
                if pricing:
                    prompt_price = pricing.get("prompt", "0")
                    completion_price = pricing.get("completion", "0")
                    price_str = f"${prompt_price}/{completion_price}"
                else:
                    price_str = "Free"

                description = model.get("description", "")
                if len(description) > 47:
                    description = description[:47] + "..."

                table.add_row(model_id, context, price_str, description)

            console.print(table)

    def display_account_dashboard(self):
        """Display account information and usage statistics."""
        if not self.api_key:
            console.print("[yellow]No API key configured.[/yellow]")
            return

        console.print("\n[bold cyan]Fetching account information...[/bold cyan]")
        account_info = self.get_account_info()

        if not account_info:
            console.print("[yellow]Could not fetch account information.[/yellow]")
            console.print("[dim]Note: Some API keys may not have access to account endpoints.[/dim]")
            return

        panel_content = []

        # Basic info
        if "label" in account_info:
            panel_content.append(f"[bold]Key Label:[/bold] {account_info['label']}")

        # Credits/Usage
        if "usage" in account_info:
            usage = account_info["usage"]
            panel_content.append(f"\n[bold cyan]Usage Statistics:[/bold cyan]")
            panel_content.append(f"  Total requests: {usage.get('requests', 'N/A')}")
            panel_content.append(f"  Total cost: ${usage.get('cost', '0.00')}")

        if "limit" in account_info:
            limit = account_info["limit"]
            panel_content.append(f"\n[bold cyan]Rate Limits:[/bold cyan]")
            panel_content.append(f"  Requests per minute: {limit.get('requests', 'N/A')}")

        # Credits remaining
        if "credits" in account_info:
            credits = account_info["credits"]
            panel_content.append(f"\n[bold green]Credits:[/bold green]")
            panel_content.append(f"  Available: ${credits}")

        if panel_content:
            console.print(Panel(
                "\n".join(panel_content),
                title="[bold]OpenRouter Account Dashboard[/bold]",
                border_style="cyan"
            ))
        else:
            console.print("[yellow]No detailed account information available.[/yellow]")


def setup_wizard() -> Optional[str]:
    """
    Interactive setup wizard to help users get started with OpenRouter.

    Returns:
        API key if successfully configured, None otherwise
    """
    # Beautiful welcome screen
    console.print()
    logo_text = Text(ascii_art.LOGO_SMALL, style="bold cyan")
    console.print(Align.center(logo_text))

    welcome_panel = Panel(
        f"[bold bright_cyan]Welcome to proCoder Setup Wizard![/bold bright_cyan]\n\n"
        f"{ascii_art.ROCKET} To get started, you'll need an OpenRouter API key\n"
        f"{ascii_art.BRAIN} OpenRouter provides access to 100+ AI models\n"
        f"{ascii_art.LIGHTNING} Simple setup in just 3 steps!",
        title=f"[bold magenta]{ascii_art.SPARKLE} Setup Wizard {ascii_art.SPARKLE}[/bold magenta]",
        border_style="bright_magenta",
        padding=(1, 2)
    )
    console.print(welcome_panel)
    console.print()

    # Step 1
    step1_panel = Panel(
        "[bold white]Get your OpenRouter API key[/bold white]\n\n"
        f"{ascii_art.BULLET} Visit: [link]https://openrouter.ai/keys[/link]\n"
        f"{ascii_art.BULLET} Sign up or log in (supports Google, GitHub, email)\n"
        f"{ascii_art.BULLET} Create a new API key\n"
        f"{ascii_art.BULLET} Copy the key (starts with 'sk-or-v1-')",
        title="[bold bright_blue]Step 1 of 3[/bold bright_blue]",
        border_style="bright_blue",
        padding=(0, 2)
    )
    console.print(step1_panel)

    open_browser = Prompt.ask(
        f"\n[bold bright_cyan]{ascii_art.ROCKET} Open OpenRouter in your browser?[/bold bright_cyan]",
        choices=["y", "n"],
        default="y"
    )

    if open_browser.lower() == "y":
        try:
            webbrowser.open(OPENROUTER_AUTH_URL)
            console.print(f"[bright_green]{ascii_art.CHECK}[/bright_green] Opened OpenRouter in your browser")
        except Exception as e:
            console.print(f"[yellow]Could not open browser:[/yellow] {e}")
            console.print(f"[dim]Please visit: {OPENROUTER_AUTH_URL}[/dim]")

    console.print()

    # Step 2
    step2_panel = Panel(
        "[bold white]Enter your API key[/bold white]\n\n"
        f"{ascii_art.BULLET} Paste your OpenRouter API key below\n"
        f"{ascii_art.BULLET} Your key will be validated automatically",
        title="[bold bright_blue]Step 2 of 3[/bold bright_blue]",
        border_style="bright_blue",
        padding=(0, 2)
    )
    console.print(step2_panel)

    api_key = Prompt.ask(
        f"\n[bright_cyan]{ascii_art.LIGHTNING} Paste your API key[/bright_cyan]",
        password=True
    )

    if not api_key or not api_key.strip():
        console.print(f"[bright_red]{ascii_art.CROSS} No API key provided. Setup cancelled.[/bright_red]")
        return None

    api_key = api_key.strip()

    # Validate the key
    console.print(f"\n[bright_cyan]{ascii_art.BRAIN} Validating API key...[/bright_cyan]")
    client = OpenRouterClient(api_key)

    if not client.validate_api_key():
        console.print(f"[bright_red]{ascii_art.CROSS} API key validation failed.[/bright_red]")
        console.print("[yellow]Please check your key and try again.[/yellow]")
        return None

    console.print(f"[bright_green]{ascii_art.CHECK} API key is valid![/bright_green]")
    console.print()

    # Step 3 - Save configuration
    step3_panel = Panel(
        "[bold white]Saving configuration[/bold white]\n\n"
        f"{ascii_art.BULLET} Saving API key to global config\n"
        f"{ascii_art.BULLET} Configuring proCoder for first use",
        title="[bold bright_blue]Step 3 of 3[/bold bright_blue]",
        border_style="bright_blue",
        padding=(0, 2)
    )
    console.print(step3_panel)
    console.print()

    # Save to global config directory (~/.procoder/.env)
    config_dir = Path.home() / ".procoder"
    config_dir.mkdir(parents=True, exist_ok=True)
    env_path = config_dir / ".env"

    # Also check for .env.example in the package
    env_example_path = Path(__file__).parent / ".env.example"

    # Create .env from .env.example if it doesn't exist
    if not env_path.exists() and env_example_path.exists():
        try:
            with open(env_example_path, "r") as f:
                env_template = f.read()
            with open(env_path, "w") as f:
                f.write(env_template)
            console.print("[green]✓ Created .env file from template[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create .env file:[/yellow] {e}")

    # Update or create .env with API key
    try:
        env_content = {}
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip().strip('"').strip("'")

        # Update API key
        env_content["OPENROUTER_API_KEY"] = api_key

        # Write back
        with open(env_path, "w") as f:
            for key, value in env_content.items():
                f.write(f'{key}="{value}"\n')

        console.print(f"[bright_green]{ascii_art.CHECK} Saved API key to {env_path}[/bright_green]")

    except Exception as e:
        console.print(f"[red]Error saving .env file:[/red] {e}")
        console.print(f"[yellow]Please manually add to .env:[/yellow] OPENROUTER_API_KEY=\"{api_key}\"")

    console.print()

    # Show account info
    account_panel = Panel(
        "[bold white]Your Account Information[/bold white]",
        title=f"[bold bright_cyan]{ascii_art.ROCKET} Account Dashboard[/bold bright_cyan]",
        border_style="bright_cyan",
        padding=(0, 2)
    )
    console.print(account_panel)
    client.display_account_dashboard()

    # Success message with recommendations
    console.print()
    success_panel = Panel(
        f"[bold bright_green]{ascii_art.SPARKLE} Setup Complete! {ascii_art.SPARKLE}[/bold bright_green]\n\n"
        f"[bold white]Recommended Models:[/bold white]\n"
        f"{ascii_art.BULLET} [bright_cyan]google/gemini-flash-1.5[/bright_cyan] - Fast, free, 1M context\n"
        f"{ascii_art.BULLET} [bright_magenta]anthropic/claude-3-sonnet[/bright_magenta] - Balanced performance\n"
        f"{ascii_art.BULLET} [bright_blue]openai/gpt-4[/bright_blue] - Highest quality\n\n"
        f"[bold white]Next Steps:[/bold white]\n"
        f"{ascii_art.ARROW} Run [bright_cyan]proCoder main[/bright_cyan] to start coding\n"
        f"{ascii_art.ARROW} Use [bright_cyan]/model list[/bright_cyan] to see all available models\n"
        f"{ascii_art.ARROW} Try [bright_cyan]/help[/bright_cyan] to see all commands",
        border_style="bright_green",
        padding=(1, 2)
    )
    console.print(success_panel)
    console.print()

    console.print("\n[dim]You can change models anytime with /model command[/dim]")
    console.print("\n[green]Ready to start coding! Run: proCoder main[/green]")

    return api_key


def quick_login() -> Optional[str]:
    """
    Quick login flow for existing users.

    Returns:
        API key if successful, None otherwise
    """
    console.print(Panel(
        "[bold cyan]OpenRouter Quick Login[/bold cyan]\n\n"
        "Enter your API key to get started.",
        border_style="cyan"
    ))

    api_key = Prompt.ask(
        "[cyan]OpenRouter API Key[/cyan]",
        password=True
    )

    if not api_key or not api_key.strip():
        return None

    api_key = api_key.strip()

    # Validate
    console.print("\n[dim]Validating...[/dim]")
    client = OpenRouterClient(api_key)

    if client.validate_api_key():
        console.print("[green]✓ Successfully authenticated![/green]")

        # Save to global config directory (~/.procoder/.env)
        config_dir = Path.home() / ".procoder"
        config_dir.mkdir(parents=True, exist_ok=True)
        env_path = config_dir / ".env"

        try:
            env_content = {}
            if env_path.exists():
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env_content[key.strip()] = value.strip().strip('"').strip("'")

            env_content["OPENROUTER_API_KEY"] = api_key

            with open(env_path, "w") as f:
                for key, value in env_content.items():
                    f.write(f'{key}="{value}"\n')

            console.print(f"[green]✓ Saved to {env_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save .env:[/yellow] {e}")

        return api_key
    else:
        console.print("[red]✗ Invalid API key[/red]")
        return None


def check_api_key_and_prompt() -> Optional[str]:
    """
    Check if API key exists, and prompt user to set up if not.

    Returns:
        API key if configured, None if user cancels
    """
    # Check environment variable
    api_key = os.getenv("OPENROUTER_API_KEY")

    if api_key and api_key.strip():
        # Validate existing key
        client = OpenRouterClient(api_key.strip())
        if client.validate_api_key():
            return api_key.strip()
        else:
            console.print("[yellow]Warning: Existing API key is invalid.[/yellow]")

    # No valid key found - prompt user
    console.print("\n[yellow]No valid OpenRouter API key found.[/yellow]")

    choice = Prompt.ask(
        "\n[bold cyan]What would you like to do?[/bold cyan]",
        choices=["setup", "login", "cancel"],
        default="setup"
    )

    if choice == "setup":
        return setup_wizard()
    elif choice == "login":
        return quick_login()
    else:
        console.print("[yellow]Setup cancelled.[/yellow]")
        return None


# Global client instance
_openrouter_client: Optional[OpenRouterClient] = None


def get_openrouter_client() -> Optional[OpenRouterClient]:
    """Get the global OpenRouter client instance."""
    return _openrouter_client


def initialize_openrouter_client(api_key: str) -> OpenRouterClient:
    """Initialize the OpenRouter client."""
    global _openrouter_client
    _openrouter_client = OpenRouterClient(api_key)
    return _openrouter_client
