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
import requests

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

        # Create categorized view
        categories = {}
        for model in models:
            model_id = model.get("id", "")
            provider = model_id.split("/")[0] if "/" in model_id else "other"
            if provider not in categories:
                categories[provider] = []
            categories[provider].append(model)

        # Display by category
        for provider, provider_models in sorted(categories.items()):
            console.print(f"\n[bold cyan]═══ {provider.upper()} Models ═══[/bold cyan]")

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=40)
            table.add_column("Context", justify="right")
            table.add_column("Pricing", justify="right")
            table.add_column("Description", width=50)

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
    console.print(Panel(
        "[bold cyan]Welcome to proCoder![/bold cyan]\n\n"
        "To get started, you'll need an OpenRouter API key.\n"
        "OpenRouter provides access to 100+ AI models through a single API.",
        title="Setup Wizard",
        border_style="green"
    ))

    console.print("\n[bold]Step 1: Get your OpenRouter API key[/bold]")
    console.print("  1. Visit: https://openrouter.ai/keys")
    console.print("  2. Sign up or log in (supports Google, GitHub, email)")
    console.print("  3. Create a new API key")
    console.print("  4. Copy the key (starts with 'sk-or-v1-')")

    open_browser = Prompt.ask(
        "\n[bold cyan]Open OpenRouter in your browser?[/bold cyan]",
        choices=["y", "n"],
        default="y"
    )

    if open_browser.lower() == "y":
        try:
            webbrowser.open(OPENROUTER_AUTH_URL)
            console.print("[green]✓[/green] Opened OpenRouter in your browser")
        except Exception as e:
            console.print(f"[yellow]Could not open browser:[/yellow] {e}")
            console.print(f"[dim]Please visit: {OPENROUTER_AUTH_URL}[/dim]")

    console.print("\n[bold]Step 2: Enter your API key[/bold]")
    api_key = Prompt.ask(
        "[cyan]Paste your OpenRouter API key[/cyan]",
        password=True
    )

    if not api_key or not api_key.strip():
        console.print("[red]No API key provided. Setup cancelled.[/red]")
        return None

    api_key = api_key.strip()

    # Validate the key
    console.print("\n[bold]Step 3: Validating API key...[/bold]")
    client = OpenRouterClient(api_key)

    if not client.validate_api_key():
        console.print("[red]✗ API key validation failed.[/red]")
        console.print("[yellow]Please check your key and try again.[/yellow]")
        return None

    console.print("[green]✓ API key is valid![/green]")

    # Save to .env file
    console.print("\n[bold]Step 4: Saving configuration...[/bold]")

    env_path = Path.cwd() / ".env"
    env_example_path = Path.cwd() / ".env.example"

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

        console.print(f"[green]✓ Saved API key to {env_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error saving .env file:[/red] {e}")
        console.print(f"[yellow]Please manually add to .env:[/yellow] OPENROUTER_API_KEY=\"{api_key}\"")

    # Show account info
    console.print("\n[bold]Step 5: Account Information[/bold]")
    client.display_account_dashboard()

    # Recommend a model
    console.print("\n[bold cyan]✓ Setup Complete![/bold cyan]")
    console.print("\n[bold]Recommended starting model:[/bold]")
    console.print("  • [cyan]google/gemini-flash-1.5[/cyan] - Fast, free, 1M context")
    console.print("  • [cyan]anthropic/claude-3-sonnet[/cyan] - Balanced performance")
    console.print("  • [cyan]openai/gpt-4[/cyan] - Highest quality")

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

        # Save to .env
        env_path = Path.cwd() / ".env"
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
