"""Extensible slash commands system for proCoder."""

import os
from pathlib import Path
from typing import Dict, Callable, Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class SlashCommand:
    """Represents a slash command."""

    def __init__(self, name: str, handler: Callable, description: str, usage: str = ""):
        """
        Initialize a slash command.

        Args:
            name: Command name (without /)
            handler: Function to handle the command
            description: Short description
            usage: Usage string
        """
        self.name = name
        self.handler = handler
        self.description = description
        self.usage = usage or f"/{name}"


class SlashCommandManager:
    """Manages slash commands and their execution."""

    def __init__(self):
        """Initialize the slash command manager."""
        self.commands: Dict[str, SlashCommand] = {}
        self.aliases: Dict[str, str] = {}  # alias -> command_name
        self.custom_commands_dir = Path.home() / ".procoder" / "commands"
        self.custom_commands_dir.mkdir(parents=True, exist_ok=True)

    def register(self, name: str, handler: Callable, description: str, usage: str = "", aliases: Optional[List[str]] = None):
        """
        Register a slash command.

        Args:
            name: Command name
            handler: Command handler function
            description: Command description
            usage: Usage information
            aliases: List of aliases for this command
        """
        command = SlashCommand(name, handler, description, usage)
        self.commands[name] = command

        if aliases:
            for alias in aliases:
                self.aliases[alias] = name

        console.print(f"[dim]Registered command: /{name}[/dim]")

    def unregister(self, name: str):
        """Unregister a command."""
        if name in self.commands:
            del self.commands[name]

            # Remove aliases
            self.aliases = {k: v for k, v in self.aliases.items() if v != name}

    def execute(self, command_line: str, context: Optional[Dict] = None) -> bool:
        """
        Execute a slash command.

        Args:
            command_line: Full command line (including /)
            context: Context dictionary with session data

        Returns:
            True if command was executed successfully
        """
        if not command_line.startswith('/'):
            return False

        # Parse command and args
        parts = command_line[1:].split(maxsplit=1)
        command_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Resolve aliases
        if command_name in self.aliases:
            command_name = self.aliases[command_name]

        # Get command
        command = self.commands.get(command_name)
        if not command:
            # Try to find custom command file
            custom_result = self._execute_custom_command(command_name, args, context)
            if custom_result is not None:
                return custom_result

            console.print(f"[red]Unknown command:[/red] /{command_name}")
            console.print("[dim]Type /help to see available commands[/dim]")
            return False

        try:
            # Execute command
            return command.handler(args, context)
        except Exception as e:
            console.print(f"[red]Error executing command /{command_name}:[/red] {e}")
            return False

    def _execute_custom_command(self, name: str, args: str, context: Optional[Dict]) -> Optional[bool]:
        """
        Execute a custom command from file.

        Args:
            name: Command name
            args: Command arguments
            context: Context dictionary

        Returns:
            True/False if custom command exists, None otherwise
        """
        # Look for command file
        command_file = self.custom_commands_dir / f"{name}.md"
        if not command_file.exists():
            command_file = self.custom_commands_dir / f"{name}.txt"

        if not command_file.exists():
            return None

        try:
            with open(command_file, 'r', encoding='utf-8') as f:
                command_content = f.read()

            console.print(f"[green]Executing custom command:[/green] /{name}")
            console.print(Panel(command_content, title=f"/{name}", border_style="cyan"))

            # If context provided, could add command content to conversation
            if context and "add_message" in context:
                message = f"Custom command /{name}"
                if args:
                    message += f" {args}"
                message += f"\n\n{command_content}"
                context["add_message"](message)

            return True

        except Exception as e:
            console.print(f"[red]Error reading custom command:[/red] {e}")
            return False

    def list_commands(self, category: Optional[str] = None):
        """
        Display all available commands.

        Args:
            category: Filter by category (if implemented)
        """
        table = Table(title="Available Slash Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Usage", style="dim")

        # Sort commands by name
        for name in sorted(self.commands.keys()):
            command = self.commands[name]
            table.add_row(f"/{name}", command.description, command.usage)

        console.print(table)

        # List custom commands
        custom_commands = list(self.custom_commands_dir.glob("*.md")) + list(self.custom_commands_dir.glob("*.txt"))
        if custom_commands:
            console.print("\n[bold cyan]Custom Commands:[/bold cyan]")
            for cmd_file in sorted(custom_commands):
                cmd_name = cmd_file.stem
                console.print(f"  [green]/{cmd_name}[/green] - Custom command")

        # List aliases
        if self.aliases:
            console.print("\n[bold cyan]Aliases:[/bold cyan]")
            for alias, target in sorted(self.aliases.items()):
                console.print(f"  [yellow]/{alias}[/yellow] → [green]/{target}[/green]")

    def get_command_help(self, name: str):
        """Display help for a specific command."""
        command = self.commands.get(name)

        if not command:
            console.print(f"[red]Unknown command:[/red] /{name}")
            return

        help_text = f"""
[bold green]/{name}[/bold green]

{command.description}

[bold]Usage:[/bold]
{command.usage}
"""

        console.print(Panel(help_text, title=f"Help: /{name}", border_style="cyan"))

    def create_custom_command(self, name: str, content: str, description: str = "") -> bool:
        """
        Create a custom slash command.

        Args:
            name: Command name
            content: Command content (markdown)
            description: Optional description

        Returns:
            True if created successfully
        """
        command_file = self.custom_commands_dir / f"{name}.md"

        if command_file.exists():
            console.print(f"[yellow]Custom command already exists:[/yellow] /{name}")
            overwrite = console.input("Overwrite? (y/n) ").lower().strip()
            if overwrite != 'y':
                return False

        try:
            full_content = content
            if description:
                full_content = f"# {description}\n\n{content}"

            with open(command_file, 'w', encoding='utf-8') as f:
                f.write(full_content)

            console.print(f"[green]Created custom command:[/green] /{name}")
            console.print(f"[dim]Location: {command_file}[/dim]")
            return True

        except Exception as e:
            console.print(f"[red]Error creating custom command:[/red] {e}")
            return False

    def delete_custom_command(self, name: str) -> bool:
        """Delete a custom command."""
        command_file = self.custom_commands_dir / f"{name}.md"
        if not command_file.exists():
            command_file = self.custom_commands_dir / f"{name}.txt"

        if not command_file.exists():
            console.print(f"[red]Custom command not found:[/red] /{name}")
            return False

        try:
            command_file.unlink()
            console.print(f"[green]Deleted custom command:[/green] /{name}")
            return True

        except Exception as e:
            console.print(f"[red]Error deleting custom command:[/red] {e}")
            return False

    def list_custom_commands(self):
        """List all custom commands with their content."""
        custom_commands = sorted(
            list(self.custom_commands_dir.glob("*.md")) +
            list(self.custom_commands_dir.glob("*.txt"))
        )

        if not custom_commands:
            console.print("[yellow]No custom commands found[/yellow]")
            console.print(f"[dim]Create commands in: {self.custom_commands_dir}[/dim]")
            return

        table = Table(title="Custom Slash Commands", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Command", style="green")
        table.add_column("File", style="blue")

        for i, cmd_file in enumerate(custom_commands, 1):
            table.add_row(str(i), f"/{cmd_file.stem}", cmd_file.name)

        console.print(table)
        console.print(f"\n[dim]Commands directory: {self.custom_commands_dir}[/dim]")

    def export_commands(self, output_file: str) -> bool:
        """Export all custom commands to a file."""
        try:
            import json

            custom_commands = {}
            for cmd_file in self.custom_commands_dir.glob("*.md"):
                with open(cmd_file, 'r', encoding='utf-8') as f:
                    custom_commands[cmd_file.stem] = f.read()

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(custom_commands, f, indent=2)

            console.print(f"[green]Exported {len(custom_commands)} commands to:[/green] {output_file}")
            return True

        except Exception as e:
            console.print(f"[red]Error exporting commands:[/red] {e}")
            return False

    def import_commands(self, input_file: str) -> bool:
        """Import custom commands from a file."""
        try:
            import json

            with open(input_file, 'r', encoding='utf-8') as f:
                custom_commands = json.load(f)

            count = 0
            for name, content in custom_commands.items():
                if self.create_custom_command(name, content):
                    count += 1

            console.print(f"[green]Imported {count} commands[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Error importing commands:[/red] {e}")
            return False
