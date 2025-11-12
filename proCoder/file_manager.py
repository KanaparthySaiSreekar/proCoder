import os
import json
from pathlib import Path
from rich.console import Console
from datetime import datetime
from typing import List, Dict, Optional
import shutil # For backups

console = Console()

# Global history for undo/redo
_change_history: List[Dict] = []
_history_index: int = -1
_max_history: int = 50

def read_file(filename: str) -> str | None:
    """Reads a file and returns its content."""
    try:
        path = Path(filename).resolve() # Get absolute path
        if not path.is_file():
            console.print(f"[red]Error: File not found:[/red] {filename}")
            return None
        # Try reading with utf-8, fallback to latin-1 for binary-ish files
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
             console.print(f"[yellow]Warning: Could not decode {filename} as UTF-8. Trying latin-1.[/yellow]")
             try:
                  with open(path, 'r', encoding='latin-1') as f:
                     return f.read()
             except Exception as e_inner:
                  console.print(f"[red]Error reading file {filename} even with latin-1:[/red] {e_inner}")
                  return None
    except Exception as e:
        console.print(f"[red]Error accessing file {filename}:[/red] {e}")
        return None

def write_file(filename: str, content: str, backup: bool = True) -> bool:
    """Writes content to a file, creating directories and optionally backing up."""
    try:
        path = Path(filename).resolve()
        path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists

        # Backup original file
        if backup and path.exists():
            backup_path = path.with_suffix(path.suffix + ".bak")
            try:
                shutil.copyfile(path, backup_path)
                console.print(f"[dim]Backup created: {backup_path}[/dim]")
            except Exception as backup_e:
                console.print(f"[yellow]Warning: Could not create backup for {filename}: {backup_e}[/yellow]")


        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        console.print(f"[red]Error writing file {filename}:[/red] {e}")
        return False

def create_new_file(filename: str, content: str) -> bool:
    """Creates a new file with the given content."""
    try:
        path = Path(filename).resolve()

        # Check if file already exists
        if path.exists():
            console.print(f"[yellow]Warning: File already exists:[/yellow] {filename}")
            return False

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write the new file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[green]Successfully created new file:[/green] {filename}")
        return True
    except Exception as e:
        console.print(f"[red]Error creating file {filename}:[/red] {e}")
        return False

def apply_changes(changes_to_apply: dict[str, str], current_files: dict[str, str]) -> list[str]:
    """Applies the approved changes to the actual files. Returns list of successfully updated files."""
    updated_filenames = []
    if not changes_to_apply:
         return updated_filenames

    console.print("\n[bold blue]Applying changes...[/bold blue]")

    # Record the change for undo
    change_record = {
        'timestamp': datetime.now().isoformat(),
        'type': 'modify',
        'files': {}
    }

    for filename, new_content in changes_to_apply.items():
        if filename not in current_files:
             console.print(f"[yellow]Warning: Trying to apply change to non-loaded file '{filename}'. Skipping.[/yellow]")
             continue

        # Store old content for undo
        old_content = current_files[filename]

        if write_file(filename, new_content, backup=True): # Backup enabled
            console.print(f"[green]Successfully updated:[/green] {filename}")
            updated_filenames.append(filename)
            change_record['files'][filename] = {
                'before': old_content,
                'after': new_content
            }
        else:
            console.print(f"[bold red]Failed to update {filename}. Halting further changes.[/bold red]")
            # Optional: Implement rollback logic here if needed
            break # Stop applying changes if one fails

    if updated_filenames:
        _add_to_history(change_record)

    return updated_filenames

def apply_new_files(new_files_to_create: dict[str, str]) -> list[str]:
    """Creates new files with approved content. Returns list of successfully created files."""
    created_filenames = []
    if not new_files_to_create:
        return created_filenames

    console.print("\n[bold blue]Creating new files...[/bold blue]")

    # Record the change for undo
    change_record = {
        'timestamp': datetime.now().isoformat(),
        'type': 'create',
        'files': {}
    }

    for filename, content in new_files_to_create.items():
        if create_new_file(filename, content):
            created_filenames.append(filename)
            change_record['files'][filename] = {
                'before': None,  # No previous content
                'after': content
            }
        else:
            console.print(f"[bold red]Failed to create {filename}.[/bold red]")

    if created_filenames:
        _add_to_history(change_record)

    return created_filenames


def _add_to_history(change_record: Dict) -> None:
    """Add a change to the undo/redo history."""
    global _change_history, _history_index

    # Remove any "future" history if we're not at the end
    if _history_index < len(_change_history) - 1:
        _change_history = _change_history[:_history_index + 1]

    # Add new change
    _change_history.append(change_record)

    # Limit history size
    if len(_change_history) > _max_history:
        _change_history.pop(0)
    else:
        _history_index += 1

    _history_index = len(_change_history) - 1


def undo() -> bool:
    """Undo the last file operation."""
    global _history_index

    if _history_index < 0 or not _change_history:
        console.print("[yellow]Nothing to undo.[/yellow]")
        return False

    change = _change_history[_history_index]
    console.print(f"[blue]Undoing {change['type']} operation from {change['timestamp']}...[/blue]")

    success = True
    for filename, file_change in change['files'].items():
        if change['type'] == 'modify':
            # Restore previous content
            if file_change['before'] is not None:
                if write_file(filename, file_change['before'], backup=False):
                    console.print(f"[green]Restored:[/green] {filename}")
                else:
                    console.print(f"[red]Failed to restore:[/red] {filename}")
                    success = False
        elif change['type'] == 'create':
            # Delete the created file
            try:
                Path(filename).unlink()
                console.print(f"[green]Deleted:[/green] {filename}")
            except Exception as e:
                console.print(f"[red]Failed to delete {filename}:[/red] {e}")
                success = False

    if success:
        _history_index -= 1

    return success


def redo() -> bool:
    """Redo the last undone file operation."""
    global _history_index

    if _history_index >= len(_change_history) - 1:
        console.print("[yellow]Nothing to redo.[/yellow]")
        return False

    _history_index += 1
    change = _change_history[_history_index]
    console.print(f"[blue]Redoing {change['type']} operation from {change['timestamp']}...[/blue]")

    success = True
    for filename, file_change in change['files'].items():
        if change['type'] in ['modify', 'create']:
            # Apply the new content
            if file_change['after'] is not None:
                if write_file(filename, file_change['after'], backup=False):
                    console.print(f"[green]Applied:[/green] {filename}")
                else:
                    console.print(f"[red]Failed to apply:[/red] {filename}")
                    success = False

    if not success:
        _history_index -= 1

    return success


def get_history_info() -> str:
    """Get information about the undo/redo history."""
    if not _change_history:
        return "[yellow]No change history available.[/yellow]"

    info = f"[cyan]Change History ({len(_change_history)} operations, current index: {_history_index}):[/cyan]\n"

    for i, change in enumerate(_change_history):
        marker = "→ " if i == _history_index else "  "
        file_count = len(change['files'])
        info += f"{marker}[dim]{i}.[/dim] {change['type']}: {file_count} file(s) at {change['timestamp']}\n"

    can_undo = _history_index >= 0
    can_redo = _history_index < len(_change_history) - 1

    info += f"\n[dim]Can undo: {can_undo}, Can redo: {can_redo}[/dim]"

    return info


def clear_history() -> None:
    """Clear the undo/redo history."""
    global _change_history, _history_index
    _change_history = []
    _history_index = -1
    console.print("[yellow]Change history cleared.[/yellow]")