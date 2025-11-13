"""
Model management for switching between different AI models dynamically.
"""
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table

console = Console()

# Popular models available on OpenRouter with their capabilities
AVAILABLE_MODELS = {
    # Anthropic Models
    "claude-3-opus": {
        "id": "anthropic/claude-3-opus",
        "name": "Claude 3 Opus",
        "speed": "⚡",
        "cost": "$$$",
        "context": "200K",
        "best_for": "Complex reasoning, long context"
    },
    "claude-3-sonnet": {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "speed": "⚡⚡",
        "cost": "$$",
        "context": "200K",
        "best_for": "Balanced performance"
    },
    "claude-3-haiku": {
        "id": "anthropic/claude-3-haiku",
        "name": "Claude 3 Haiku",
        "speed": "⚡⚡⚡",
        "cost": "$",
        "context": "200K",
        "best_for": "Fast responses"
    },

    # OpenAI Models
    "gpt-4": {
        "id": "openai/gpt-4",
        "name": "GPT-4",
        "speed": "⚡",
        "cost": "$$$",
        "context": "8K",
        "best_for": "Highest quality"
    },
    "gpt-4-turbo": {
        "id": "openai/gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "speed": "⚡⚡",
        "cost": "$$",
        "context": "128K",
        "best_for": "Long documents"
    },
    "gpt-3.5-turbo": {
        "id": "openai/gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "speed": "⚡⚡⚡",
        "cost": "$",
        "context": "16K",
        "best_for": "Fast, cheap"
    },

    # Google Models
    "gemini-pro": {
        "id": "google/gemini-pro",
        "name": "Gemini Pro",
        "speed": "⚡⚡",
        "cost": "$$",
        "context": "32K",
        "best_for": "Multimodal tasks"
    },
    "gemini-flash": {
        "id": "google/gemini-flash-1.5",
        "name": "Gemini 1.5 Flash",
        "speed": "⚡⚡⚡",
        "cost": "Free",
        "context": "1M",
        "best_for": "Huge contexts, free"
    },

    # Meta Models
    "llama-70b": {
        "id": "meta-llama/llama-3-70b-instruct",
        "name": "Llama 3 70B",
        "speed": "⚡⚡",
        "cost": "$",
        "context": "8K",
        "best_for": "Open source"
    },

    # Mistral Models
    "mistral-large": {
        "id": "mistralai/mistral-large",
        "name": "Mistral Large",
        "speed": "⚡⚡",
        "cost": "$$",
        "context": "32K",
        "best_for": "European alternative"
    },

    # Coding-specific models
    "deepseek-coder": {
        "id": "deepseek/deepseek-coder",
        "name": "DeepSeek Coder",
        "speed": "⚡⚡",
        "cost": "$",
        "context": "16K",
        "best_for": "Code generation"
    },
    "codellama-70b": {
        "id": "meta-llama/codellama-70b-instruct",
        "name": "CodeLlama 70B",
        "speed": "⚡⚡",
        "cost": "$",
        "context": "16K",
        "best_for": "Code-focused"
    }
}

# Model aliases for easier access
MODEL_ALIASES = {
    "opus": "claude-3-opus",
    "sonnet": "claude-3-sonnet",
    "haiku": "claude-3-haiku",
    "gpt4": "gpt-4",
    "gpt3": "gpt-3.5-turbo",
    "gemini": "gemini-flash",
    "llama": "llama-70b",
    "mistral": "mistral-large",
    "deepseek": "deepseek-coder",
    "codellama": "codellama-70b"
}


class ModelManager:
    """Manages model selection and switching."""

    def __init__(self, default_model: str = "gemini-flash"):
        self.current_model_key = default_model
        self.model_history = []

    def get_current_model(self) -> Dict:
        """Get the current model configuration."""
        return AVAILABLE_MODELS.get(self.current_model_key, AVAILABLE_MODELS["gemini-flash"])

    def get_current_model_id(self) -> str:
        """Get the OpenRouter model ID for API calls."""
        return self.get_current_model()["id"]

    def get_current_model_name(self) -> str:
        """Get the display name of the current model."""
        return self.get_current_model()["name"]

    def switch_model(self, model_identifier: str) -> bool:
        """
        Switch to a different model.

        Args:
            model_identifier: Model key, alias, or partial name

        Returns:
            True if switch successful, False otherwise
        """
        # Try direct key match
        if model_identifier in AVAILABLE_MODELS:
            old_model = self.get_current_model_name()
            self.model_history.append(self.current_model_key)
            self.current_model_key = model_identifier
            console.print(f"[green]Switched from {old_model} to {self.get_current_model_name()}[/green]")
            return True

        # Try alias
        if model_identifier in MODEL_ALIASES:
            return self.switch_model(MODEL_ALIASES[model_identifier])

        # Try partial match
        matches = []
        search_lower = model_identifier.lower()
        for key, model in AVAILABLE_MODELS.items():
            if search_lower in key.lower() or search_lower in model["name"].lower():
                matches.append(key)

        if len(matches) == 1:
            return self.switch_model(matches[0])
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple matches found:[/yellow]")
            for match in matches:
                model = AVAILABLE_MODELS[match]
                console.print(f"  - {match}: {model['name']}")
            console.print("[yellow]Please be more specific.[/yellow]")
            return False

        console.print(f"[red]Model '{model_identifier}' not found.[/red]")
        console.print("[yellow]Use /model list to see available models.[/yellow]")
        return False

    def list_models(self, category: Optional[str] = None):
        """Display available models in a formatted table."""
        table = Table(title="Available AI Models")
        table.add_column("Key", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Speed", justify="center")
        table.add_column("Cost", justify="center")
        table.add_column("Context", justify="right")
        table.add_column("Best For")
        table.add_column("Current", justify="center")

        for key, model in AVAILABLE_MODELS.items():
            # Filter by category if specified
            if category:
                if category.lower() not in model["name"].lower():
                    continue

            is_current = "✓" if key == self.current_model_key else ""
            table.add_row(
                key,
                model["name"],
                model["speed"],
                model["cost"],
                model["context"],
                model["best_for"],
                is_current
            )

        console.print(table)
        console.print("\n[dim]Usage: /model <key or alias>[/dim]")
        console.print(f"[dim]Current model: {self.get_current_model_name()}[/dim]")

    def get_model_info(self, model_key: Optional[str] = None) -> Dict:
        """Get detailed information about a model."""
        if model_key is None:
            model_key = self.current_model_key

        if model_key in MODEL_ALIASES:
            model_key = MODEL_ALIASES[model_key]

        return AVAILABLE_MODELS.get(model_key, self.get_current_model())

    def previous_model(self) -> bool:
        """Switch back to the previous model."""
        if not self.model_history:
            console.print("[yellow]No previous model in history.[/yellow]")
            return False

        previous = self.model_history.pop()
        old_model = self.get_current_model_name()
        self.current_model_key = previous
        console.print(f"[green]Switched back from {old_model} to {self.get_current_model_name()}[/green]")
        return True

    def get_recommended_model(self, task_type: str) -> str:
        """Recommend a model based on task type."""
        recommendations = {
            "code": "deepseek-coder",
            "fast": "gemini-flash",
            "quality": "claude-3-opus",
            "long": "gemini-flash",
            "cheap": "gemini-flash",
            "reasoning": "claude-3-opus"
        }

        return recommendations.get(task_type.lower(), "gemini-flash")


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def initialize_model_manager(default_model: str = "gemini-flash"):
    """Initialize the model manager with a default model."""
    global _model_manager
    _model_manager = ModelManager(default_model)
    return _model_manager
