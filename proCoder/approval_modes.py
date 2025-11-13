"""Approval modes for controlling what the AI can do without user confirmation."""

from enum import Enum
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import os

console = Console()


class ApprovalMode(Enum):
    """Different approval modes for AI actions."""
    READ_ONLY = "read_only"
    AUTO = "auto"
    FULL_ACCESS = "full_access"


class ApprovalManager:
    """Manages approval modes and permissions for AI actions."""

    def __init__(self, initial_mode: ApprovalMode = ApprovalMode.AUTO, working_dir: Optional[str] = None):
        """
        Initialize the approval manager.

        Args:
            initial_mode: Initial approval mode
            working_dir: Working directory for auto mode restrictions
        """
        self.current_mode = initial_mode
        self.working_dir = os.path.abspath(working_dir) if working_dir else os.getcwd()
        console.print(f"[blue]Approval mode set to:[/blue] [bold]{self.current_mode.value}[/bold]")

    def set_mode(self, mode: ApprovalMode):
        """Change the approval mode."""
        old_mode = self.current_mode
        self.current_mode = mode

        console.print(f"[green]Approval mode changed:[/green] {old_mode.value} → [bold]{mode.value}[/bold]")
        self.display_mode_info()

    def get_mode(self) -> ApprovalMode:
        """Get the current approval mode."""
        return self.current_mode

    def display_mode_info(self):
        """Display information about the current mode."""
        mode_info = {
            ApprovalMode.READ_ONLY: """
[bold yellow]Read Only Mode[/bold yellow]

The AI can:
  ✓ Read files
  ✓ Search code
  ✓ Provide suggestions

The AI cannot:
  ✗ Edit files
  ✗ Create files
  ✗ Run commands
  ✗ Stage/commit changes

[dim]Use this mode for exploration and consultation.[/dim]
""",
            ApprovalMode.AUTO: """
[bold green]Auto Mode[/bold green] (Default)

The AI can:
  ✓ Read files anywhere
  ✓ Edit files in working directory
  ✓ Create files in working directory
  ✓ Run safe commands in working directory
  ✓ Stage/commit changes in working directory

The AI will ask before:
  ? Editing files outside working directory
  ? Network access
  ? Potentially dangerous commands

[dim]Use this mode for normal development work.[/dim]
""",
            ApprovalMode.FULL_ACCESS: """
[bold red]Full Access Mode[/bold red] ⚠️

The AI can:
  ✓ Read/edit/create files anywhere
  ✓ Run any command
  ✓ Network access
  ✓ System-wide operations

[bold]Warning:[/bold] Only use in trusted environments!

[dim]Use this mode only when you fully trust the task and repository.[/dim]
"""
        }

        console.print(Panel(mode_info[self.current_mode], border_style=self._get_mode_color()))

    def _get_mode_color(self) -> str:
        """Get the color for the current mode."""
        return {
            ApprovalMode.READ_ONLY: "yellow",
            ApprovalMode.AUTO: "green",
            ApprovalMode.FULL_ACCESS: "red"
        }[self.current_mode]

    def can_read_file(self, filepath: str) -> bool:
        """Check if AI can read a file."""
        # All modes allow reading
        return True

    def can_edit_file(self, filepath: str) -> bool:
        """Check if AI can edit a file without asking."""
        if self.current_mode == ApprovalMode.READ_ONLY:
            return False

        if self.current_mode == ApprovalMode.FULL_ACCESS:
            return True

        # AUTO mode: check if file is in working directory
        abs_filepath = os.path.abspath(filepath)
        return abs_filepath.startswith(self.working_dir)

    def can_create_file(self, filepath: str) -> bool:
        """Check if AI can create a file without asking."""
        if self.current_mode == ApprovalMode.READ_ONLY:
            return False

        if self.current_mode == ApprovalMode.FULL_ACCESS:
            return True

        # AUTO mode: check if file is in working directory
        abs_filepath = os.path.abspath(filepath)
        return abs_filepath.startswith(self.working_dir)

    def can_delete_file(self, filepath: str) -> bool:
        """Check if AI can delete a file without asking."""
        # Deletion always requires confirmation in AUTO mode
        if self.current_mode in [ApprovalMode.READ_ONLY, ApprovalMode.AUTO]:
            return False

        return True  # FULL_ACCESS

    def can_run_command(self, command: str) -> bool:
        """Check if AI can run a command without asking."""
        if self.current_mode == ApprovalMode.READ_ONLY:
            return False

        if self.current_mode == ApprovalMode.FULL_ACCESS:
            return True

        # AUTO mode: check if command is safe
        return self._is_safe_command(command)

    def _is_safe_command(self, command: str) -> bool:
        """Check if a command is considered safe."""
        # List of safe commands (read-only or git operations)
        safe_commands = [
            'git status', 'git log', 'git diff', 'git show',
            'git branch', 'git ls-files', 'git rev-parse',
            'ls', 'pwd', 'cat', 'head', 'tail', 'grep',
            'find', 'which', 'echo', 'printf'
        ]

        # Git write operations are safe in auto mode (within repo)
        safe_git_write = ['git add', 'git commit', 'git push', 'git pull', 'git fetch']

        command_lower = command.lower().strip()

        # Check if command starts with any safe command
        for safe_cmd in safe_commands:
            if command_lower.startswith(safe_cmd):
                return True

        for safe_git in safe_git_write:
            if command_lower.startswith(safe_git):
                return True

        return False

    def can_access_network(self) -> bool:
        """Check if AI can access the network without asking."""
        # Network access only in FULL_ACCESS mode
        return self.current_mode == ApprovalMode.FULL_ACCESS

    def request_permission(self, action: str, details: str = "") -> bool:
        """
        Request permission for an action from the user.

        Args:
            action: Description of the action
            details: Additional details about the action

        Returns:
            True if permission granted
        """
        console.print(f"\n[yellow]Permission required:[/yellow] [bold]{action}[/bold]")
        if details:
            console.print(f"[dim]{details}[/dim]")

        response = console.input("[yellow]Allow this action?[/yellow] ([bold green]y[/bold green]/[bold red]n[/bold red]) ").lower().strip()
        return response in ['y', 'yes']

    def check_file_operation(self, operation: str, filepath: str, auto_approve: bool = False) -> bool:
        """
        Check if a file operation is allowed.

        Args:
            operation: Type of operation (read/edit/create/delete)
            filepath: Path to the file
            auto_approve: Whether to auto-approve in AUTO mode

        Returns:
            True if operation is allowed
        """
        if operation == "read":
            return self.can_read_file(filepath)

        elif operation == "edit":
            if self.current_mode == ApprovalMode.READ_ONLY:
                console.print(f"[red]Cannot edit files in READ_ONLY mode:[/red] {filepath}")
                return False

            if self.can_edit_file(filepath):
                return True

            # Ask for permission
            if auto_approve:
                return True

            return self.request_permission(
                f"Edit file outside working directory",
                f"File: {filepath}\nWorking dir: {self.working_dir}"
            )

        elif operation == "create":
            if self.current_mode == ApprovalMode.READ_ONLY:
                console.print(f"[red]Cannot create files in READ_ONLY mode:[/red] {filepath}")
                return False

            if self.can_create_file(filepath):
                return True

            # Ask for permission
            if auto_approve:
                return True

            return self.request_permission(
                f"Create file outside working directory",
                f"File: {filepath}\nWorking dir: {self.working_dir}"
            )

        elif operation == "delete":
            if self.current_mode == ApprovalMode.READ_ONLY:
                console.print(f"[red]Cannot delete files in READ_ONLY mode:[/red] {filepath}")
                return False

            # Always ask for delete confirmation unless FULL_ACCESS
            if self.current_mode == ApprovalMode.FULL_ACCESS:
                return True

            return self.request_permission(
                f"Delete file",
                f"File: {filepath}"
            )

        return False

    def check_command_execution(self, command: str, auto_approve: bool = False) -> bool:
        """
        Check if a command execution is allowed.

        Args:
            command: Command to execute
            auto_approve: Whether to auto-approve safe commands

        Returns:
            True if execution is allowed
        """
        if self.current_mode == ApprovalMode.READ_ONLY:
            console.print(f"[red]Cannot run commands in READ_ONLY mode:[/red] {command}")
            return False

        if self.can_run_command(command):
            return True

        # Ask for permission
        if auto_approve:
            return True

        return self.request_permission(
            f"Run command",
            f"Command: {command}"
        )

    def display_modes_table(self):
        """Display a comparison table of all approval modes."""
        table = Table(title="Approval Modes", show_header=True, header_style="bold cyan")

        table.add_column("Action", style="white")
        table.add_column("Read Only", style="yellow", justify="center")
        table.add_column("Auto (Default)", style="green", justify="center")
        table.add_column("Full Access", style="red", justify="center")

        actions = [
            ("Read files", "✓", "✓", "✓"),
            ("Edit files in working dir", "✗", "✓", "✓"),
            ("Edit files outside working dir", "✗", "Ask", "✓"),
            ("Create files in working dir", "✗", "✓", "✓"),
            ("Create files outside working dir", "✗", "Ask", "✓"),
            ("Delete files", "✗", "Ask", "✓"),
            ("Run safe commands", "✗", "✓", "✓"),
            ("Run all commands", "✗", "Ask", "✓"),
            ("Network access", "✗", "Ask", "✓"),
            ("Git operations", "✗", "✓", "✓"),
        ]

        for action, read_only, auto, full in actions:
            table.add_row(action, read_only, auto, full)

        console.print(table)
        console.print(f"\n[bold]Current mode:[/bold] {self.current_mode.value}")

    @staticmethod
    def parse_mode(mode_str: str) -> Optional[ApprovalMode]:
        """Parse a mode string to ApprovalMode enum."""
        mode_map = {
            "read-only": ApprovalMode.READ_ONLY,
            "readonly": ApprovalMode.READ_ONLY,
            "read": ApprovalMode.READ_ONLY,
            "auto": ApprovalMode.AUTO,
            "full-access": ApprovalMode.FULL_ACCESS,
            "full": ApprovalMode.FULL_ACCESS,
            "fulls": ApprovalMode.FULL_ACCESS,
        }

        return mode_map.get(mode_str.lower().strip())
