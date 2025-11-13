import subprocess
import os
import time
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


def _retry_with_backoff(func, max_retries: int = 4, initial_delay: float = 2.0, operation_name: str = "operation"):
    """Helper to retry operations with exponential backoff."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            result = func()
            if result and result.returncode == 0:
                return result
            # If command failed but not due to network, don't retry
            if result and result.stderr and not any(err in result.stderr.lower() for err in ['network', 'connection', 'timeout', 'could not resolve', 'failed to connect']):
                return result
        except Exception as e:
            if attempt < max_retries - 1:
                console.print(f"[yellow]{operation_name} failed (attempt {attempt + 1}/{max_retries}): {e}[/yellow]")
                console.print(f"[yellow]Retrying in {delay}s...[/yellow]")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                console.print(f"[red]{operation_name} failed after {max_retries} attempts: {e}[/red]")
                return None
    return None


def get_current_branch(repo_root: str) -> Optional[str]:
    """Gets the name of the current branch."""
    result = _run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_root)
    if result and result.returncode == 0:
        return result.stdout.strip()
    return None


def get_remote_url(repo_root: str, remote: str = 'origin') -> Optional[str]:
    """Gets the URL of the specified remote."""
    result = _run_git_command(['remote', 'get-url', remote], cwd=repo_root, check=False)
    if result and result.returncode == 0:
        return result.stdout.strip()
    return None


def fetch_from_remote(repo_root: str, remote: str = 'origin', branch: Optional[str] = None, retry: bool = True) -> bool:
    """Fetches from remote repository with retry logic."""
    args = ['fetch', remote]
    if branch:
        args.append(branch)

    console.print(f"[blue]Fetching from {remote}" + (f" branch {branch}" if branch else "") + "...[/blue]")

    if retry:
        result = _retry_with_backoff(
            lambda: _run_git_command(args, cwd=repo_root, check=False),
            operation_name=f"Git fetch {remote}" + (f" {branch}" if branch else "")
        )
    else:
        result = _run_git_command(args, cwd=repo_root, check=False)

    if result and result.returncode == 0:
        console.print(f"[green]Successfully fetched from {remote}[/green]")
        return True
    else:
        console.print(f"[red]Failed to fetch from {remote}[/red]")
        return False


def pull_from_remote(repo_root: str, remote: str = 'origin', branch: Optional[str] = None, retry: bool = True) -> bool:
    """Pulls from remote repository with retry logic."""
    args = ['pull', remote]
    if branch:
        args.append(branch)

    console.print(f"[blue]Pulling from {remote}" + (f" branch {branch}" if branch else "") + "...[/blue]")

    if retry:
        result = _retry_with_backoff(
            lambda: _run_git_command(args, cwd=repo_root, check=False),
            operation_name=f"Git pull {remote}" + (f" {branch}" if branch else "")
        )
    else:
        result = _run_git_command(args, cwd=repo_root, check=False)

    if result and result.returncode == 0:
        console.print(f"[green]Successfully pulled from {remote}[/green]")
        return True
    else:
        console.print(f"[red]Failed to pull from {remote}[/red]")
        if result and result.stderr:
            console.print(f"[red]Error: {result.stderr}[/red]")
        return False


def push_to_remote(repo_root: str, remote: str = 'origin', branch: Optional[str] = None,
                   set_upstream: bool = False, retry: bool = True, force: bool = False) -> bool:
    """
    Pushes to remote repository with retry logic.

    Args:
        repo_root: Root directory of the git repository
        remote: Remote name (default: 'origin')
        branch: Branch name (if None, uses current branch)
        set_upstream: Whether to set upstream tracking (-u flag)
        retry: Whether to retry on network failures
        force: Whether to force push (use with caution!)

    Returns:
        True if push succeeded, False otherwise
    """
    if branch is None:
        branch = get_current_branch(repo_root)
        if not branch:
            console.print("[red]Could not determine current branch[/red]")
            return False

    # CRITICAL: Validate branch starts with 'claude/' and session ID format
    if not branch.startswith('claude/'):
        console.print(f"[red]Error: Branch '{branch}' must start with 'claude/'[/red]")
        console.print("[yellow]This is required for push authentication.[/yellow]")
        return False

    # Check if branch matches expected format: claude/.*-[A-Za-z0-9]{20,}
    import re
    if not re.match(r'^claude/.*-[A-Za-z0-9]{20,}$', branch):
        console.print(f"[red]Error: Branch '{branch}' must end with a valid session ID (20+ alphanumeric characters)[/red]")
        console.print("[yellow]Expected format: claude/<description>-<SESSION_ID>[/yellow]")
        return False

    args = ['push']
    if set_upstream:
        args.extend(['-u', remote, branch])
    else:
        args.extend([remote, branch])

    if force:
        # Check if pushing to main/master with force
        if branch in ['main', 'master']:
            console.print("[bold red]WARNING: Force pushing to main/master is dangerous![/bold red]")
            confirm = console.input("Are you absolutely sure? Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                console.print("[yellow]Force push cancelled.[/yellow]")
                return False
        args.append('--force')

    upstream_flag = " with upstream tracking" if set_upstream else ""
    console.print(f"[blue]Pushing to {remote}/{branch}{upstream_flag}...[/blue]")

    if retry:
        result = _retry_with_backoff(
            lambda: _run_git_command(args, cwd=repo_root, check=False),
            operation_name=f"Git push {remote} {branch}"
        )
    else:
        result = _run_git_command(args, cwd=repo_root, check=False)

    if result and result.returncode == 0:
        console.print(f"[green]Successfully pushed to {remote}/{branch}[/green]")
        return True
    else:
        console.print(f"[red]Failed to push to {remote}/{branch}[/red]")
        if result and result.stderr:
            # Check for 403 error
            if '403' in result.stderr:
                console.print("[red]HTTP 403 Forbidden - This likely means:[/red]")
                console.print(f"[yellow]  - Branch must start with 'claude/' (current: {branch})[/yellow]")
                console.print(f"[yellow]  - Branch must end with session ID (20+ chars)[/yellow]")
            console.print(f"[red]Error: {result.stderr}[/red]")
        return False


def get_git_status(repo_root: str) -> Optional[str]:
    """Gets the current git status."""
    result = _run_git_command(['status', '--short'], cwd=repo_root)
    if result and result.returncode == 0:
        return result.stdout
    return None


def has_uncommitted_changes(repo_root: str) -> bool:
    """Checks if there are uncommitted changes in the repository."""
    status = get_git_status(repo_root)
    return status is not None and len(status.strip()) > 0


def get_commit_log(repo_root: str, max_count: int = 10, oneline: bool = True) -> Optional[str]:
    """Gets recent commit history."""
    args = ['log']
    if oneline:
        args.append('--oneline')
    args.extend([f'-{max_count}'])

    result = _run_git_command(args, cwd=repo_root)
    if result and result.returncode == 0:
        return result.stdout
    return None


def get_diff_stats(repo_root: str, from_ref: str = 'HEAD', to_ref: Optional[str] = None) -> Optional[str]:
    """Gets diff statistics between two refs."""
    args = ['diff', '--stat', from_ref]
    if to_ref:
        args.append(to_ref)

    result = _run_git_command(args, cwd=repo_root)
    if result and result.returncode == 0:
        return result.stdout
    return None