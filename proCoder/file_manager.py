import os
from pathlib import Path
from rich.console import Console
import shutil # For backups

console = Console()

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

def apply_changes(changes_to_apply: dict[str, str], current_files: dict[str, str]) -> list[str]:
    """Applies the approved changes to the actual files. Returns list of successfully updated files."""
    updated_filenames = []
    if not changes_to_apply:
         return updated_filenames

    console.print("\n[bold blue]Applying changes...[/bold blue]")
    for filename, new_content in changes_to_apply.items():
        if filename not in current_files:
             console.print(f"[yellow]Warning: Trying to apply change to non-loaded file '{filename}'. Skipping.[/yellow]")
             continue

        if write_file(filename, new_content, backup=True): # Backup enabled
            console.print(f"[green]Successfully updated:[/green] {filename}")
            updated_filenames.append(filename)
        else:
            console.print(f"[bold red]Failed to update {filename}. Halting further changes.[/bold red]")
            # Optional: Implement rollback logic here if needed
            break # Stop applying changes if one fails

    return updated_filenames