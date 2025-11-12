import re
import difflib
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from typing import Dict, List, Optional

from . import git_utils # Import git utils

console = Console()

# Improved regex to capture optional language and filename hints reliably
# Allows filenames with spaces if quoted, handles various hint formats
CODE_BLOCK_PATTERN = re.compile(
    r"```(?:\w+)?\s*(?:(?:filename|path|file)\s*[:=]?\s*(?:\"([^\"]+)\"|'([^']+)'|(\S+)))?\s*\n" # Language and filename hint
    r"(.*?)\n"  # Code content itself
    r"```",     # Closing fence
    re.DOTALL | re.IGNORECASE
)

def extract_code_changes(response_text: str, known_filenames: List[str]) -> tuple[Dict[str, str], Dict[str, str]]:
    """
    Extracts code blocks intended for specific files from the AI's response.
    Prioritizes explicit filename hints within the code block fence.

    Returns:
        tuple: (changes_dict, new_files_dict)
            - changes_dict: Changes to existing loaded files
            - new_files_dict: Proposed new files to create
    """
    changes = {}
    potential_new_files = {}

    for match in CODE_BLOCK_PATTERN.finditer(response_text):
        # Extract potential filename hints (quoted or unquoted)
        hint1, hint2, hint3, code_content = match.groups()
        filename_hint = hint1 or hint2 or hint3
        code_content = code_content.strip() # Remove leading/trailing whitespace

        target_filename = None

        if filename_hint:
            normalized_hint = filename_hint.strip().replace("\\", "/") # Normalize separators
            # Exact match first
            for fname in known_filenames:
                if fname == normalized_hint:
                    target_filename = fname
                    break
            # Partial match (suffix) if no exact match found
            if not target_filename:
                for fname in known_filenames:
                     # Check if normalized hint is suffix of known filename or vice versa
                     if fname.endswith(normalized_hint) or normalized_hint.endswith(fname.split('/')[-1]):
                         target_filename = fname
                         console.print(f"[dim]Matched hint '{normalized_hint}' to loaded file '{fname}' (partial match).[/dim]")
                         break

            if not target_filename:
                 # Suggest as a potential new file if hint looks like a path
                 if "/" in normalized_hint or "." in normalized_hint:
                      potential_new_files[normalized_hint] = code_content
                      console.print(f"[dim]Code block found with hint for potential new file: '{normalized_hint}'.[/dim]")
                 else:
                      console.print(f"[yellow]Warning:[/yellow] Code block hint '{normalized_hint}' did not match any loaded file. Ignoring.")
                 continue # Skip to next block
        else:
            # If no hint, and only one file is loaded, assume it's for that file.
            if len(known_filenames) == 1:
                target_filename = known_filenames[0]
                console.print(f"[dim]Code block found without hint, assuming it's for the only loaded file: {target_filename}[/dim]")
            else:
                 console.print("[yellow]Warning:[/yellow] Code block found without filename hint and multiple files loaded. Cannot determine target file. Ignoring.")
                 continue # Skip ambiguous blocks

        if target_filename:
            if target_filename in changes:
                console.print(f"[yellow]Warning:[/yellow] Multiple code blocks modifying '{target_filename}'. Using the last one found.")
            changes[target_filename] = code_content

    return changes, potential_new_files


def generate_diff(filename: str, old_content: str, new_content: str, repo_root: Optional[str]) -> str:
    """Generates a unified diff string, preferring git diff if available."""
    # Try git diff first if in a repo and file exists
    if repo_root and os.path.exists(filename):
        # Git diff requires writing the new content to a temp file or using stdin,
        # or diffing against the index/worktree. Easiest is python difflib here
        # unless we want complex git interaction. Let's stick to difflib for display consistency.
        # git_diff_text = git_utils.get_git_diff(filename, repo_root) # This diffs against HEAD/index
        # If we want diff against current file content, difflib is better.
        pass # Fall through to difflib

    # Use Python's difflib
    diff = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{os.path.basename(filename)}", # Use basename for cleaner diff header
        tofile=f"b/{os.path.basename(filename)}",
        lineterm='\n'
    )
    return "".join(diff)


def prompt_for_changes(
    extracted_changes: Dict[str, str],
    current_files: Dict[str, str],
    repo_root: Optional[str]
    ) -> Dict[str, str]:
    """Shows diffs and asks the user whether to apply each change."""
    approved_changes = {}
    if not extracted_changes:
        return approved_changes

    console.print(Panel("[bold cyan]Proposed Code Changes[/bold cyan]", expand=False))

    sorted_filenames = sorted(extracted_changes.keys())

    for filename in sorted_filenames:
        if filename not in current_files:
            continue # Should be filtered, but double-check

        old_content = current_files[filename]
        new_content = extracted_changes[filename]

        # Generate diff using our utility function
        diff_text = generate_diff(filename, old_content, new_content, repo_root)

        if not diff_text.strip():
            console.print(f"\n[dim]AI suggested no textual changes for {filename}.[/dim]")
            continue

        console.print(f"\nChanges for [bold magenta]{filename}[/bold magenta]:")
        # Use Rich Syntax for highlighting the diff
        syntax = Syntax(diff_text, "diff", theme="default", line_numbers=False, word_wrap=True)
        console.print(syntax)
        console.print("-" * 40) # Separator

        while True:
            response = console.input(f"Apply changes to {filename}? ([bold green]y[/bold green]es/[bold red]n[/bold red]o/[bold blue]d[/bold blue]etails/[bold yellow]q[/bold yellow]uit asking) ").lower().strip()
            if response == 'y':
                approved_changes[filename] = new_content
                break
            elif response == 'n':
                console.print(f"[yellow]Skipping changes for {filename}.[/yellow]")
                break
            elif response == 'd':
                 # Show full new file content
                 console.print(f"\n[bold cyan]--- Full proposed content for {filename} ---[/bold cyan]")
                 lang = filename.split('.')[-1] if '.' in filename else 'text'
                 syntax_full = Syntax(new_content, lang, theme="default", line_numbers=True, word_wrap=False)
                 console.print(syntax_full)
                 console.print(f"[bold cyan]--- End proposed content for {filename} ---[/bold cyan]")
                 # Loop back to ask y/n/d/q again
            elif response == 'q':
                console.print("[yellow]Aborting change application process.[/yellow]")
                return {} # Return empty dict, no changes approved from this point
            else:
                console.print("[red]Invalid input.[/red] Please enter y, n, d, or q.")

    if not approved_changes:
        console.print("\n[yellow]No changes were approved.[/yellow]")

    return approved_changes


def prompt_for_new_files(new_files: Dict[str, str], repo_root: Optional[str]) -> Dict[str, str]:
    """Shows proposed new files and asks the user whether to create each one."""
    approved_new_files = {}
    if not new_files:
        return approved_new_files

    console.print(Panel("[bold green]Proposed New Files[/bold green]", expand=False))

    sorted_filenames = sorted(new_files.keys())

    for filename in sorted_filenames:
        content = new_files[filename]

        console.print(f"\nNew file: [bold magenta]{filename}[/bold magenta]")
        console.print(f"[dim]Size: {len(content)} characters, {len(content.splitlines())} lines[/dim]")

        # Show preview of content
        lang = filename.split('.')[-1] if '.' in filename else 'text'
        syntax = Syntax(content, lang, theme="default", line_numbers=True, word_wrap=False)
        console.print(syntax)
        console.print("-" * 40) # Separator

        while True:
            response = console.input(f"Create new file {filename}? ([bold green]y[/bold green]es/[bold red]n[/bold red]o/[bold yellow]q[/bold yellow]uit asking) ").lower().strip()
            if response == 'y':
                approved_new_files[filename] = content
                break
            elif response == 'n':
                console.print(f"[yellow]Skipping creation of {filename}.[/yellow]")
                break
            elif response == 'q':
                console.print("[yellow]Aborting new file creation process.[/yellow]")
                return {} # Return empty dict, no files approved from this point
            else:
                console.print("[red]Invalid input.[/red] Please enter y, n, or q.")

    if not approved_new_files:
        console.print("\n[yellow]No new files were approved.[/yellow]")

    return approved_new_files


def limit_history(history: list[dict], max_messages: int):
    """
    Basic history truncation based on message count, preserving system prompts.
    """
    system_prompts = [m for m in history if m.get('role') == 'system']
    user_assistant_msgs = [m for m in history if m.get('role') in ['user', 'assistant', 'model']]

    if len(user_assistant_msgs) > max_messages:
        # Keep the N most recent user/assistant messages
        truncated_messages = user_assistant_msgs[-max_messages:]
        history[:] = system_prompts + truncated_messages # Modify list in-place
        console.print(f"[dim]History truncated to the last {max_messages} user/assistant messages.[/dim]")