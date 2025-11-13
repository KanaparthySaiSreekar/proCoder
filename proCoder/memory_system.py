"""
Persistent memory system for maintaining context across sessions.
Inspired by Claude Code's memory capabilities and MCP memory servers.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()

class MemorySystem:
    """Manages persistent memory across sessions."""

    def __init__(self, memory_file: str = ".procoder_memory.json"):
        self.memory_file = memory_file
        self.memory: Dict[str, Any] = {
            "facts": {},  # Key-value facts about the project
            "preferences": {},  # User preferences
            "patterns": [],  # Recurring patterns or decisions
            "architecture": {},  # High-level architecture notes
            "recent_changes": [],  # Recent important changes
            "todos": [],  # Project todos and tasks
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        self.load()

    def load(self) -> bool:
        """Load memory from file."""
        if not os.path.exists(self.memory_file):
            return False

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self.memory.update(loaded)
            console.print(f"[dim]Loaded project memory from {self.memory_file}[/dim]")
            return True
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load memory file:[/yellow] {e}")
            return False

    def save(self) -> bool:
        """Save memory to file."""
        try:
            self.memory["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            console.print(f"[red]Error saving memory:[/red] {e}")
            return False

    def add_fact(self, key: str, value: str, category: str = "general"):
        """Add or update a fact about the project."""
        if category not in self.memory["facts"]:
            self.memory["facts"][category] = {}

        self.memory["facts"][category][key] = {
            "value": value,
            "added": datetime.now().isoformat()
        }
        console.print(f"[green]Remembered:[/green] {key} = {value}")
        self.save()

    def get_fact(self, key: str, category: str = "general") -> Optional[str]:
        """Retrieve a fact."""
        if category in self.memory["facts"] and key in self.memory["facts"][category]:
            return self.memory["facts"][category][key]["value"]
        return None

    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.memory["preferences"][key] = {
            "value": value,
            "updated": datetime.now().isoformat()
        }
        console.print(f"[green]Preference set:[/green] {key} = {value}")
        self.save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        if key in self.memory["preferences"]:
            return self.memory["preferences"][key]["value"]
        return default

    def add_pattern(self, pattern: str, context: str = ""):
        """Record a recurring pattern or decision."""
        pattern_entry = {
            "pattern": pattern,
            "context": context,
            "recorded": datetime.now().isoformat()
        }
        self.memory["patterns"].append(pattern_entry)
        console.print(f"[green]Pattern recorded:[/green] {pattern}")
        self.save()

    def add_architecture_note(self, component: str, description: str):
        """Add architectural information."""
        self.memory["architecture"][component] = {
            "description": description,
            "updated": datetime.now().isoformat()
        }
        console.print(f"[green]Architecture note added:[/green] {component}")
        self.save()

    def log_change(self, description: str, files: List[str] = None):
        """Log an important change."""
        change_entry = {
            "description": description,
            "files": files or [],
            "timestamp": datetime.now().isoformat()
        }
        self.memory["recent_changes"].append(change_entry)

        # Keep only last 20 changes
        if len(self.memory["recent_changes"]) > 20:
            self.memory["recent_changes"] = self.memory["recent_changes"][-20:]

        self.save()

    def add_todo(self, task: str, priority: str = "normal"):
        """Add a project todo."""
        todo_entry = {
            "task": task,
            "priority": priority,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        self.memory["todos"].append(todo_entry)
        console.print(f"[green]Todo added:[/green] {task}")
        self.save()

    def complete_todo(self, task_index: int) -> bool:
        """Mark a todo as completed."""
        if 0 <= task_index < len(self.memory["todos"]):
            self.memory["todos"][task_index]["completed"] = True
            self.memory["todos"][task_index]["completed_at"] = datetime.now().isoformat()
            console.print(f"[green]Todo completed![/green]")
            self.save()
            return True
        return False

    def get_context_summary(self) -> str:
        """Generate a summary of stored memory for AI context."""
        summary_parts = []

        # Project facts
        if self.memory["facts"]:
            summary_parts.append("## Project Facts")
            for category, facts in self.memory["facts"].items():
                summary_parts.append(f"### {category.capitalize()}")
                for key, data in facts.items():
                    summary_parts.append(f"- **{key}**: {data['value']}")

        # Architecture
        if self.memory["architecture"]:
            summary_parts.append("\n## Architecture")
            for component, data in self.memory["architecture"].items():
                summary_parts.append(f"- **{component}**: {data['description']}")

        # Preferences
        if self.memory["preferences"]:
            summary_parts.append("\n## User Preferences")
            for key, data in self.memory["preferences"].items():
                summary_parts.append(f"- **{key}**: {data['value']}")

        # Patterns
        if self.memory["patterns"]:
            summary_parts.append("\n## Recurring Patterns")
            # Show last 5 patterns
            for pattern in self.memory["patterns"][-5:]:
                summary_parts.append(f"- {pattern['pattern']}")
                if pattern["context"]:
                    summary_parts.append(f"  Context: {pattern['context']}")

        # Recent changes
        if self.memory["recent_changes"]:
            summary_parts.append("\n## Recent Important Changes")
            for change in self.memory["recent_changes"][-5:]:
                summary_parts.append(f"- {change['description']}")
                if change["files"]:
                    summary_parts.append(f"  Files: {', '.join(change['files'][:3])}")

        # Active todos
        active_todos = [t for t in self.memory["todos"] if not t["completed"]]
        if active_todos:
            summary_parts.append("\n## Active Tasks")
            for todo in active_todos[:5]:
                priority_marker = "🔴" if todo["priority"] == "high" else "🟡" if todo["priority"] == "normal" else "🟢"
                summary_parts.append(f"- {priority_marker} {todo['task']}")

        if not summary_parts:
            return ""

        return "\n".join(summary_parts)

    def display_memory(self, section: Optional[str] = None):
        """Display stored memory to the user."""
        if section == "facts" or section is None:
            if self.memory["facts"]:
                console.print("\n[bold cyan]Project Facts:[/bold cyan]")
                for category, facts in self.memory["facts"].items():
                    console.print(f"  [yellow]{category.capitalize()}:[/yellow]")
                    for key, data in facts.items():
                        console.print(f"    • {key}: {data['value']}")

        if section == "preferences" or section is None:
            if self.memory["preferences"]:
                console.print("\n[bold cyan]Preferences:[/bold cyan]")
                for key, data in self.memory["preferences"].items():
                    console.print(f"  • {key}: {data['value']}")

        if section == "architecture" or section is None:
            if self.memory["architecture"]:
                console.print("\n[bold cyan]Architecture:[/bold cyan]")
                for component, data in self.memory["architecture"].items():
                    console.print(f"  • {component}: {data['description']}")

        if section == "patterns" or section is None:
            if self.memory["patterns"]:
                console.print("\n[bold cyan]Patterns (last 10):[/bold cyan]")
                for pattern in self.memory["patterns"][-10:]:
                    console.print(f"  • {pattern['pattern']}")
                    if pattern["context"]:
                        console.print(f"    [dim]{pattern['context']}[/dim]")

        if section == "todos" or section is None:
            if self.memory["todos"]:
                console.print("\n[bold cyan]Tasks:[/bold cyan]")
                for i, todo in enumerate(self.memory["todos"]):
                    status = "✓" if todo["completed"] else " "
                    priority_marker = "🔴" if todo["priority"] == "high" else "🟡" if todo["priority"] == "normal" else "🟢"
                    console.print(f"  [{i}] [{status}] {priority_marker} {todo['task']}")

        if section == "changes" or section is None:
            if self.memory["recent_changes"]:
                console.print("\n[bold cyan]Recent Changes:[/bold cyan]")
                for change in self.memory["recent_changes"][-10:]:
                    console.print(f"  • {change['description']}")
                    if change["files"]:
                        console.print(f"    [dim]Files: {', '.join(change['files'][:3])}[/dim]")

    def clear_section(self, section: str) -> bool:
        """Clear a specific section of memory."""
        if section in self.memory and section != "metadata":
            if isinstance(self.memory[section], dict):
                self.memory[section] = {}
            elif isinstance(self.memory[section], list):
                self.memory[section] = []
            console.print(f"[yellow]Cleared {section} from memory.[/yellow]")
            self.save()
            return True
        return False

    def export_memory(self, export_file: str) -> bool:
        """Export memory to a different file."""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Memory exported to {export_file}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error exporting memory:[/red] {e}")
            return False


# Global memory system instance
_memory_system: Optional[MemorySystem] = None


def get_memory_system() -> Optional[MemorySystem]:
    """Get the global memory system instance."""
    return _memory_system


def initialize_memory_system(git_repo_root: Optional[str] = None) -> MemorySystem:
    """Initialize the memory system."""
    global _memory_system

    # Store memory file in git repo root if available, otherwise in current directory
    memory_file = ".procoder_memory.json"
    if git_repo_root:
        memory_file = os.path.join(git_repo_root, memory_file)

    _memory_system = MemorySystem(memory_file)
    return _memory_system
