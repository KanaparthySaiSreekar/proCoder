"""
Model management for switching between different AI models dynamically.
Fetches real-time models from OpenRouter API.
"""
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import requests
import time

from . import ascii_art
from . import config

console = Console()

# Cache for fetched models
_models_cache = None
_cache_timestamp = 0
CACHE_DURATION = 3600  # 1 hour


def fetch_models_from_openrouter() -> List[Dict]:
    """Fetch available models from OpenRouter API."""
    global _models_cache, _cache_timestamp

    # Return cached models if still valid
    if _models_cache and (time.time() - _cache_timestamp) < CACHE_DURATION:
        return _models_cache

    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            _models_cache = data.get("data", [])
            _cache_timestamp = time.time()
            return _models_cache
    except Exception as e:
        console.print(f"[dim]Could not fetch models from OpenRouter: {e}[/dim]")

    return []


def get_free_models(models: List[Dict]) -> List[Dict]:
    """Filter for free models."""
    free_models = []
    for model in models:
        pricing = model.get("pricing", {})
        prompt_cost = float(pricing.get("prompt", "1"))
        completion_cost = float(pricing.get("completion", "1"))

        if prompt_cost == 0 and completion_cost == 0:
            free_models.append(model)

    return free_models


def format_cost(pricing: Dict) -> str:
    """Format pricing information."""
    if not pricing:
        return "?"

    prompt = float(pricing.get("prompt", "0"))
    completion = float(pricing.get("completion", "0"))

    if prompt == 0 and completion == 0:
        return "FREE"

    # Calculate average cost per 1M tokens
    avg_cost = (prompt + completion) / 2

    if avg_cost < 0.5:
        return "$"
    elif avg_cost < 5:
        return "$$"
    elif avg_cost < 20:
        return "$$$"
    else:
        return "$$$$"


def format_context(context_length: int) -> str:
    """Format context length for display."""
    if context_length >= 1000000:
        return f"{context_length // 1000000}M"
    elif context_length >= 1000:
        return f"{context_length // 1000}K"
    else:
        return str(context_length)


class ModelManager:
    """Manages model selection and switching."""

    def __init__(self, default_model: str = "google/gemini-2.0-flash-exp:free"):
        self.current_model_id = default_model
        self.model_history = []
        self.models = []
        self._refresh_models()

    def _refresh_models(self):
        """Refresh the models list from OpenRouter."""
        self.models = fetch_models_from_openrouter()

    def get_current_model_id(self) -> str:
        """Get the OpenRouter model ID for API calls."""
        return self.current_model_id

    def get_current_model_name(self) -> str:
        """Get the display name of the current model."""
        for model in self.models:
            if model.get("id") == self.current_model_id:
                return model.get("name", self.current_model_id)
        return self.current_model_id

    def switch_model(self, model_identifier: str) -> bool:
        """
        Switch to a different model.

        Args:
            model_identifier: Model ID or partial name

        Returns:
            True if switch successful, False otherwise
        """
        # Refresh models if cache is old
        if time.time() - _cache_timestamp > CACHE_DURATION:
            self._refresh_models()

        # Try exact ID match
        for model in self.models:
            if model.get("id") == model_identifier:
                old_model = self.get_current_model_name()
                self.model_history.append(self.current_model_id)
                self.current_model_id = model_identifier
                console.print(f"[green]✓ Switched from {old_model} to {model.get('name')}[/green]")
                return True

        # Try partial match
        matches = []
        search_lower = model_identifier.lower()
        for model in self.models:
            model_id = model.get("id", "").lower()
            model_name = model.get("name", "").lower()
            if search_lower in model_id or search_lower in model_name:
                matches.append(model)

        if len(matches) == 1:
            return self.switch_model(matches[0]["id"])
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple matches found for '{model_identifier}':[/yellow]\n")
            for i, match in enumerate(matches[:10], 1):
                console.print(f"  {i}. {match['id']} - {match.get('name', 'Unknown')}")
            console.print("\n[yellow]Please be more specific with the model ID.[/yellow]")
            return False

        console.print(f"[red]Model '{model_identifier}' not found.[/red]")
        console.print("[yellow]Use /model list to see available models.[/yellow]")
        return False

    def list_models(self, filter_text: Optional[str] = None, show_free_only: bool = False):
        """Display available models in a formatted table."""
        # Refresh models if needed
        if time.time() - _cache_timestamp > CACHE_DURATION:
            self._refresh_models()

        if not self.models:
            console.print("[yellow]Could not fetch models. Please check your internet connection.[/yellow]")
            return

        # Filter models
        filtered_models = self.models

        if show_free_only:
            filtered_models = get_free_models(filtered_models)

        if filter_text:
            filter_lower = filter_text.lower()
            filtered_models = [
                m for m in filtered_models
                if filter_lower in m.get("id", "").lower() or filter_lower in m.get("name", "").lower()
            ]

        if not filtered_models:
            console.print(f"[yellow]No models found matching '{filter_text}'[/yellow]")
            return

        # Header
        filter_desc = f" ({filter_text})" if filter_text else ""
        free_desc = " (FREE ONLY)" if show_free_only else ""
        header_panel = Panel(
            f"[bold bright_cyan]{len(filtered_models)} Models Available{filter_desc}{free_desc}[/bold bright_cyan]\n"
            f"{ascii_art.LIGHTNING} Switch with: /model <model-id>",
            title=f"[bold magenta]{ascii_art.BRAIN} OpenRouter Models[/bold magenta]",
            border_style="bright_magenta",
            padding=(0, 2)
        )
        console.print(header_panel)
        console.print()

        # Create table
        table = Table(show_header=True, header_style="bold magenta", border_style="bright_blue")
        table.add_column("Model ID", style="bright_cyan", no_wrap=False, max_width=50)
        table.add_column("Name", style="white", max_width=30)
        table.add_column("Context", justify="right", style="bright_blue")
        table.add_column("Cost", justify="center", style="bright_green")
        table.add_column("Active", justify="center", style="bright_green")

        # Show first 50 models
        for model in filtered_models[:50]:
            model_id = model.get("id", "Unknown")
            name = model.get("name", "Unknown")
            context = model.get("context_length", 0)
            pricing = model.get("pricing", {})

            is_current = f"[bright_green]{ascii_art.CHECK}[/bright_green]" if model_id == self.current_model_id else ""

            table.add_row(
                model_id,
                name,
                format_context(context),
                format_cost(pricing),
                is_current
            )

        console.print(table)

        if len(filtered_models) > 50:
            console.print(f"\n[dim]Showing 50 of {len(filtered_models)} models. Use filters to narrow down.[/dim]")

        # Footer
        current_model_name = self.get_current_model_name()
        console.print()
        footer_panel = Panel(
            f"[bold white]Usage:[/bold white]\n"
            f"  /model <model-id>              Switch to a model\n"
            f"  /model list free               Show only free models\n"
            f"  /model list <search>           Filter models\n"
            f"  /model back                    Return to previous model\n\n"
            f"[bold bright_cyan]Current:[/bold bright_cyan] {current_model_name}\n"
            f"[bold bright_cyan]ID:[/bold bright_cyan] [dim]{self.current_model_id}[/dim]",
            border_style="bright_blue",
            padding=(0, 2)
        )
        console.print(footer_panel)

    def get_model_info(self, model_id: Optional[str] = None) -> Dict:
        """Get detailed information about a model."""
        if model_id is None:
            model_id = self.current_model_id

        for model in self.models:
            if model.get("id") == model_id:
                # Format the model info for display
                pricing = model.get("pricing", {})
                context = model.get("context_length", 0)

                return {
                    "id": model.get("id", "Unknown"),
                    "name": model.get("name", "Unknown"),
                    "speed": "Fast" if "flash" in model.get("id", "").lower() else "Standard",
                    "cost": format_cost(pricing),
                    "context": format_context(context),
                    "best_for": model.get("description", "General purpose tasks")[:100]
                }

        return {
            "id": model_id,
            "name": "Unknown",
            "speed": "Unknown",
            "cost": "Unknown",
            "context": "Unknown",
            "best_for": "Unknown"
        }

    def previous_model(self) -> bool:
        """Switch back to the previous model."""
        if not self.model_history:
            console.print("[yellow]No previous model in history.[/yellow]")
            return False

        previous = self.model_history.pop()
        old_model = self.get_current_model_name()
        self.current_model_id = previous
        console.print(f"[green]✓ Switched back from {old_model} to {self.get_current_model_name()}[/green]")
        return True


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def initialize_model_manager(default_model: str = "google/gemini-2.0-flash-exp:free"):
    """Initialize the model manager with a default model."""
    global _model_manager
    _model_manager = ModelManager(default_model)
    return _model_manager
