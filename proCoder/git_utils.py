import subprocess
import os
from pathlib import Path
from rich.console import Console
from typing import Optional, List

console = Console()

def _run_git_command(args: List[str], cwd: Optional[str] = None, check: bool = True) -> Optional[subprocess.CompletedProcess]:
    """Helper to run git commands and handle common errors."""
    try:
        # Ensure Git command exists
        subprocess.run(['git', '--version'], capture_output=True, check=True, cwd=cwd)

        # Run the actual command
        process = subprocess.run(['git'] + args, capture_output=True, text=True, check=check, cwd=cwd)
        if check and process.returncode != 0:
             console.print(f"[red]Git command failed:[/red] {' '.join(['git'] + args)}")
             console.print(f"[red]Stderr:[/red]\n{process.stderr}")
             return None
        if process.stderr and not process.stderr.startswith("warning:"): # Print stderr unless it's just a warning
             console.print(f"[yellow]Git stderr:[/yellow]\n{process.stderr}")
        return process
    except FileNotFoundError:
        console.print("[bold red]Error: 'git' command not found. Is Git installed and in your PATH?[/bold red]")
        return None
    except subprocess.CalledProcessError as e:
        # This is usually caught by check=True logic above, but handle just in case
        console.print(f"[red]Git command failed:[/red] {' '.join(['git'] + args)}")
        if e.stderr:
             console.print(f"[red]Stderr:[/red]\n{e.stderr}")
        if e.stdout:
             console.print(f"[red]Stdout:[/red]\n{e.stdout}")
        return None
    except Exception as e:
        console.print(f"[red]An unexpected error occurred running Git command:[/red] {e}")
        return None


def get_repo_root(path: Optional[str] = None) -> Optional[str]:
    """Finds the root directory of the git repository containing the path."""
    # Start from specified path or current working directory
    start_path = Path(path).resolve() if path else Path.cwd()

    # If start_path is a file, start from its parent directory
    if start_path.is_file():
        start_path = start_path.parent

    result = _run_git_command(['rev-parse', '--show-toplevel'], cwd=str(start_path), check=False) # Check False as it fails outside repo
    if result and result.returncode == 0:
        return result.stdout.strip()
    return None


def is_git_repo(path: Optional[str] = None) -> bool:
    """Checks if the given path is inside a Git repository."""
    return get_repo_root(path) is not None


def get_tracked_files(repo_root: str) -> List[str]:
    """Gets a list of all files tracked by Git."""
    result = _run_git_command(['ls-files'], cwd=repo_root)
    if result:
        # Return absolute paths
        return [os.path.join(repo_root, f) for f in result.stdout.splitlines()]
    return []


def get_staged_files(repo_root: str) -> List[str]:
    """Gets a list of files currently staged for commit."""
    result = _run_git_command(['diff', '--name-only', '--cached'], cwd=repo_root)
    if result:
        # Return absolute paths
        return [os.path.join(repo_root, f) for f in result.stdout.splitlines()]
    return []


def get_git_diff(filename: str, repo_root: str, staged: bool = False) -> Optional[str]:
    """Gets the git diff for a specific file (staged or unstaged)."""
    relative_path = os.path.relpath(filename, repo_root)
    args = ['diff', '--no-color'] # Use no-color for parsing, rely on Rich for display
    if staged:
        args.append('--cached')
    args.append('--') # Important separator
    args.append(relative_path)

    result = _run_git_command(args, cwd=repo_root)
    return result.stdout if result else None


def stage_files(filenames: List[str], repo_root: str) -> bool:
    """Stages the specified files."""
    if not filenames:
        return True
    relative_paths = [os.path.relpath(f, repo_root) for f in filenames]
    console.print(f"[blue]Staging files:[/blue] {', '.join(relative_paths)}")
    result = _run_git_command(['add', '--'] + relative_paths, cwd=repo_root)
    return result is not None and result.returncode == 0


def commit_changes(repo_root: str, message: Optional[str] = None) -> bool:
    """Commits currently staged changes."""
    if not message:
        # Simple default message
        staged = get_staged_files(repo_root)
        if not staged:
             console.print("[yellow]No changes staged to commit.[/yellow]")
             return True # Not an error, just nothing to do
        message = f"proCoder AI changes:\n\n- Updated {len(staged)} file(s)"

    console.print(f"[blue]Committing staged changes with message:[/blue]\n{message}")
    result = _run_git_command(['commit', '-m', message], cwd=repo_root)
    return result is not None and result.returncode == 0