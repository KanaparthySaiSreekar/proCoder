import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from typing_extensions import Annotated # Use typing.Annotated in Python 3.9+
from typing import List, Optional
import sys
import os
# import readline # Enables history and better editing in input()

import sys
# Conditionally import readline for non-Windows platforms
if sys.platform != "win32":
    try:
        import readline # Enables history and better editing in input()
    except ImportError:
        # Handle case where readline might be missing even on non-windows
        # though this is uncommon for standard distributions.
        print("Warning: 'readline' module not found, line editing features may be limited.", file=sys.stderr)

# (The rest of your main.py code continues below)

from pathlib import Path

# Import local modules
from . import config
from . import ai_client
from . import file_manager
from . import utils
from . import git_utils

# --- Setup ---
app = typer.Typer(help="proCoder: AI assistant for code editing in your terminal.")
console = Console()

# --- Global State (Consider using a State Class for larger applications) ---
conversation_history = []
# Store absolute paths for consistency
loaded_files: dict[str, str] = {} # {absolute_filepath: content}
git_repo_root: Optional[str] = None # Store root path if detected

# --- Helper Functions ---

def load_file_content(filepath: str) -> bool:
    """Loads or reloads content for a single file."""
    global loaded_files
    abs_path = str(Path(filepath).resolve()) # Ensure absolute path

    if not os.path.exists(abs_path):
        console.print(f"[yellow]Warning: File not found, cannot load:[/yellow] {filepath}")
        # Remove if it was previously loaded but now deleted
        if abs_path in loaded_files:
             del loaded_files[abs_path]
        return False

    content = file_manager.read_file(abs_path)
    if content is not None:
        if abs_path not in loaded_files:
             console.print(f"[green]Loaded file:[/green] {os.path.relpath(abs_path)}") # Show relative path for clarity
        else:
             console.print(f"[blue]Reloaded file:[/blue] {os.path.relpath(abs_path)}")
        loaded_files[abs_path] = content
        return True
    else:
        # Error reading file (permission etc.)
        console.print(f"[red]Failed to read file content:[/red] {filepath}")
        if abs_path in loaded_files:
             del loaded_files[abs_path] # Remove if failed to reload
        return False

def add_initial_context_to_prompt():
    """Adds system prompts, Git context, and loaded file content."""
    global conversation_history
    if conversation_history: # Avoid adding multiple times
        return

    # 1. System Prompt (Role/Instructions for the AI)
    system_prompt = (
        "You are proCoder, an expert AI programming assistant integrated into the user's terminal. "
        "Your goal is to help the user understand, modify, and generate code based on the provided files and conversation. "
        "When asked to make changes:\n"
        "1. Respond with clear explanations of the changes.\n"
        "2. Provide the complete, updated code for the relevant file(s) enclosed in Markdown code blocks.\n"
        "3. **Crucially**, use a filename hint in the code block fence, like ```python filename=\"path/to/your/file.py\"\n...code...\n``` or similar.\n"
        "4. If modifying multiple files, use separate code blocks for each.\n"
        "5. If the user's request is unclear, ask clarifying questions."
    )
    conversation_history.append({"role": "system", "content": system_prompt})

    # 2. Git Context (if in a repo)
    if git_repo_root:
        git_context = f"The user is working inside a Git repository located at: {git_repo_root}\n"
        # Optional: Add branch name, recent commits, etc.
        # branch_process = git_utils._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=git_repo_root)
        # if branch_process: git_context += f"Current branch: {branch_process.stdout.strip()}\n"
        conversation_history.append({"role": "system", "content": git_context.strip()})

    # 3. File Context
    if loaded_files:
        file_prompt_content = "The user has loaded the following files into the context:\n\n"
        for abs_path, content in loaded_files.items():
            relative_path = os.path.relpath(abs_path, git_repo_root) if git_repo_root else os.path.basename(abs_path)
            file_prompt_content += f"--- File: {relative_path} ---\n"
            # Include only a portion if file is very large? For now, include all.
            file_prompt_content += f"```\n{content}\n```\n\n"

        conversation_history.append({"role": "system", "content": file_prompt_content.strip()})
        console.print(f"[dim]Added {len(loaded_files)} file(s) and system prompts to conversation context.[/dim]")


def process_user_message(user_input: str):
    """Handles user input, calls AI, processes response, handles changes & Git."""
    global conversation_history
    global loaded_files

    # Add user message to history (OpenAI format: 'user')
    conversation_history.append({"role": "user", "content": user_input})

    # Prepare the prompt data for the API call (adds context if needed)
    prompt_data = ai_client.prepare_prompt_for_api(conversation_history, loaded_files, user_input)

    # --- Streaming AI Response ---
    full_response = ""
    console.print(f"[bold blue]AI ({config.MODEL_NAME}):[/bold blue]", end="")
    try:
        with Live(console=console, refresh_per_second=10, vertical_overflow="visible") as live:
            accumulated_response_markdown = ""
            for chunk in ai_client.stream_ai_response(prompt_data, config.MODEL_NAME):
                full_response += chunk
                # Update live display with Markdown rendering
                # Note: Frequent Markdown parsing can be slow; update less often if needed
                accumulated_response_markdown += chunk
                # Limit re-rendering frequency if performance issues arise
                # if time.time() - last_render_time > 0.1:
                live.update(Markdown(accumulated_response_markdown))
                # last_render_time = time.time()

            # Ensure the final complete response is displayed
            live.update(Markdown(full_response))
        print() # Add a newline after the stream finishes

    except Exception as e:
        console.print(f"\n[bold red]Error during AI interaction:[/bold red] {e}")
        # Remove the last user message and potentially incomplete AI response from history
        if conversation_history and conversation_history[-1]["role"] == "user":
            conversation_history.pop()
        return # Abort processing this message

    # Add AI response to history (OpenAI format: 'assistant')
    conversation_history.append({"role": "assistant", "content": full_response})

    # --- Extract and Apply Code Changes ---
    # Pass absolute paths of known files
    extracted_changes = utils.extract_code_changes(full_response, list(loaded_files.keys()))

    if extracted_changes:
        # Pass repo_root to use git diff if available
        approved_changes = utils.prompt_for_changes(extracted_changes, loaded_files, git_repo_root)

        if approved_changes:
            updated_abs_paths = file_manager.apply_changes(approved_changes, loaded_files)

            if updated_abs_paths:
                console.print(f"\n[green]Successfully applied changes to {len(updated_abs_paths)} file(s).[/green]")
                # Reload content of updated files into memory
                console.print("[blue]Reloading updated file content...[/blue]")
                reload_ok_count = 0
                for abs_path in updated_abs_paths:
                     if load_file_content(abs_path): # Use the helper to reload
                          reload_ok_count += 1
                if reload_ok_count == len(updated_abs_paths):
                     console.print("[green]In-memory file context updated.[/green]")
                else:
                     console.print("[yellow]Warning: Some files failed to reload after changes.[/yellow]")


                # --- Git Integration ---
                if git_repo_root:
                    handle_git_operations(updated_abs_paths)
            else:
                console.print("\n[yellow]No changes were ultimately applied to files.[/yellow]")

    # Limit history size
    utils.limit_history(conversation_history, config.MAX_HISTORY_MESSAGES)


def handle_git_operations(updated_abs_paths: List[str]):
    """Handles staging and committing changes after files are updated."""
    global git_repo_root
    if not git_repo_root or not updated_abs_paths:
        return

    # Filter to only paths actually within the repo (should always be true if logic is correct)
    paths_in_repo = [p for p in updated_abs_paths if p.startswith(git_repo_root)]
    if not paths_in_repo:
        return

    staged_ok = False
    # Auto-stage or ask
    if config.GIT_AUTO_STAGE:
        console.print("[blue]Auto-staging enabled. Staging changes...[/blue]")
        staged_ok = git_utils.stage_files(paths_in_repo, git_repo_root)
    else:
         relative_paths_str = ", ".join([os.path.relpath(p, git_repo_root) for p in paths_in_repo])
         stage_prompt = f"\nStage the changes to [{relative_paths_str}]? ([bold green]y[/bold green]/[bold red]n[/bold red]) "
         response = console.input(stage_prompt).lower().strip()
         if response == 'y':
             staged_ok = git_utils.stage_files(paths_in_repo, git_repo_root)
             if staged_ok:
                  console.print("[green]Changes staged successfully.[/green]")
             else:
                  console.print("[red]Failed to stage changes.[/red]")
         else:
              console.print("[yellow]Changes not staged.[/yellow]")


    # Auto-commit or ask (only if staging happened or was requested)
    if staged_ok:
        if config.GIT_AUTO_COMMIT:
            console.print("[blue]Auto-commit enabled. Committing staged changes...[/blue]")
            # Generate a basic commit message
            commit_message = f"proCoder AI updates for: {', '.join([os.path.basename(p) for p in paths_in_repo])}"
            commit_ok = git_utils.commit_changes(git_repo_root, commit_message)
            if commit_ok:
                 console.print("[green]Changes committed successfully.[/green]")
            else:
                 console.print("[red]Failed to commit changes.[/red]")
        else:
             commit_prompt = "Commit the staged changes? ([bold green]y[/bold green]/[bold red]n[/bold red]) "
             response = console.input(commit_prompt).lower().strip()
             if response == 'y':
                 # Ask for commit message
                 commit_message = console.input("Enter commit message (leave blank for default): ").strip()
                 commit_ok = git_utils.commit_changes(git_repo_root, commit_message if commit_message else None)
                 if commit_ok:
                      console.print("[green]Changes committed successfully.[/green]")
                 else:
                      console.print("[red]Failed to commit changes.[/red]")
             else:
                  console.print("[yellow]Staged changes not committed.[/yellow]")


# --- Typer Commands ---

@app.callback()
def callback(ctx: typer.Context):
    """
    proCoder: AI assistant for code editing. Manages session state.
    """
    global git_repo_root
    # Detect Git repo based on CWD *before* processing files
    git_repo_root = git_utils.get_repo_root()
    if git_repo_root:
        console.print(f"[dim]Detected Git repository root: {git_repo_root}[/dim]")
    else:
        console.print("[dim]Not inside a Git repository.[/dim]")


@app.command()
def main(
    files: Annotated[Optional[List[str]], typer.Argument(
        help="Path(s) to code files to load into the context.",
        show_default=False)] = None,
    # TODO: Add more options like --model, --yes (auto-apply diff), etc.
):
    """
    Starts an interactive chat session for AI-assisted coding.

    Load initial files by providing their paths as arguments.
    """
    global loaded_files
    global git_repo_root

    console.print(Panel("[bold magenta]Welcome to proCoder AI Assistant![/bold magenta]", expand=False, border_style="blue"))

    initial_load_success = True
    if files:
        console.print("[blue]Loading initial files...[/blue]")
        for f_path in files:
            # If inside a git repo, try to resolve relative to repo root if path doesn't exist directly
            potential_path = Path(f_path)
            resolved_path = potential_path.resolve() # Try resolving first

            if not resolved_path.exists() and git_repo_root and not potential_path.is_absolute():
                 path_in_repo = Path(git_repo_root) / f_path
                 if path_in_repo.exists():
                      resolved_path = path_in_repo.resolve()
                      console.print(f"[dim]Resolved relative path '{f_path}' inside Git repo to '{resolved_path}'[/dim]")
                 else:
                      console.print(f"[yellow]Warning: File not found:[/yellow] {f_path} (also checked relative to Git root)")
                      initial_load_success = False
                      continue
            elif not resolved_path.exists():
                  console.print(f"[yellow]Warning: File not found:[/yellow] {f_path}")
                  initial_load_success = False
                  continue

            if not load_file_content(str(resolved_path)):
                initial_load_success = False
        if not initial_load_success:
             console.print("[yellow]Some initial files could not be loaded.[/yellow]")


    # Add system prompts and file context *after* loading initial files
    add_initial_context_to_prompt()


    console.print("\nType your message or command. Available commands:")
    console.print("  /load <path>... : Load or reload file(s) into context.")
    console.print("  /drop <path>... : Remove file(s) from context.")
    console.print("  /files          : List currently loaded files.")
    console.print("  /clear          : Clear conversation history.")
    console.print("  /context        : Show the current context being sent to the AI (for debugging).")
    console.print("  /help           : Show this help message again.")
    console.print("  /quit or /exit  : Exit the assistant.")

    # --- Main Interaction Loop ---
    while True:
        try:
            # Use relpath for display if possible
            loaded_files_display = [os.path.relpath(p, git_repo_root) if git_repo_root else os.path.basename(p) for p in loaded_files]
            prompt_prefix = f"[cyan]Files: {loaded_files_display}[/cyan]\n" if loaded_files_display else ""
            user_input = console.input(f"{prompt_prefix}[bold green]>>> [/bold green]")
        except EOFError: # Handle Ctrl+D
            console.print("\n[bold yellow]EOF detected. Exiting.[/bold yellow]")
            break
        except KeyboardInterrupt: # Handle Ctrl+C
             console.print("\n[bold yellow]Interrupt detected. Type /quit or /exit to leave.[/bold yellow]")
             continue # Continue to next loop iteration

        command = user_input.lower().strip()

        # --- Command Handling ---
        if command in ["/quit", "/exit"]:
            break
        elif command.startswith("/load"):
            paths_to_load = user_input.split()[1:]
            if not paths_to_load:
                 console.print("[yellow]Usage: /load <path1> [path2] ...[/yellow]")
                 continue
            console.print(f"[blue]Loading files:[/blue] {paths_to_load}")
            loaded_count = 0
            for f_path in paths_to_load:
                  # Resolve path similar to initial load
                  potential_path = Path(f_path)
                  resolved_path = potential_path.resolve()
                  if not resolved_path.exists() and git_repo_root and not potential_path.is_absolute():
                     path_in_repo = Path(git_repo_root) / f_path
                     if path_in_repo.exists(): resolved_path = path_in_repo.resolve()
                     else:
                          console.print(f"[yellow]Warning: File not found:[/yellow] {f_path}")
                          continue
                  elif not resolved_path.exists():
                        console.print(f"[yellow]Warning: File not found:[/yellow] {f_path}")
                        continue

                  if load_file_content(str(resolved_path)):
                       loaded_count += 1
            if loaded_count > 0:
                  # TODO: Decide if we should re-inject file context into history here
                  # For simplicity now, we rely on prepare_prompt to add context as needed
                  console.print(f"[green]Successfully loaded/reloaded {loaded_count} file(s).[/green]")
            else:
                  console.print("[yellow]No files were loaded.[/yellow]")
            continue # Skip AI processing for this command
        elif command.startswith("/drop"):
            paths_to_drop = user_input.split()[1:]
            if not paths_to_drop:
                 console.print("[yellow]Usage: /drop <path1> [path2] ...[/yellow]")
                 continue
            dropped_count = 0
            for f_path in paths_to_drop:
                # Find the absolute path matching the input (could be relative or basename)
                path_to_remove = None
                abs_f_path_resolved = str(Path(f_path).resolve()) # Resolve input path first
                for abs_loaded_path in list(loaded_files.keys()): # Iterate over copy of keys
                    rel_loaded_path = os.path.relpath(abs_loaded_path, git_repo_root) if git_repo_root else os.path.basename(abs_loaded_path)
                    # Match against absolute path, relative path from repo, or basename
                    if abs_loaded_path == abs_f_path_resolved or \
                       (git_repo_root and rel_loaded_path == f_path) or \
                       os.path.basename(abs_loaded_path) == f_path:
                       path_to_remove = abs_loaded_path
                       break # Found match

                if path_to_remove and path_to_remove in loaded_files:
                     del loaded_files[path_to_remove]
                     console.print(f"[green]Dropped file from context:[/green] {os.path.relpath(path_to_remove)}")
                     dropped_count += 1
                else:
                     console.print(f"[yellow]File not found in loaded context:[/yellow] {f_path}")
            if dropped_count > 0:
                 # TODO: Maybe add a message to history indicating file drop?
                 pass
            continue # Skip AI processing
        elif command == "/files":
            if not loaded_files:
                console.print("[cyan]No files currently loaded in context.[/cyan]")
            else:
                 console.print("[cyan]Currently loaded files:[/cyan]")
                 for i, abs_path in enumerate(loaded_files.keys()):
                     relative_path = os.path.relpath(abs_path, git_repo_root) if git_repo_root else os.path.basename(abs_path)
                     console.print(f"  {i+1}. {relative_path} ({abs_path})")
            continue # Skip AI processing
        elif command == "/clear":
             conversation_history.clear()
             loaded_files.clear() # Also clear loaded files? Or just history? Let's clear both.
             console.print("[yellow]Conversation history and loaded files cleared.[/yellow]")
             # Re-add initial system prompts
             add_initial_context_to_prompt()
             continue # Skip AI processing
        elif command == "/context":
             console.print("[bold yellow]--- Current Context (Prepared for next AI call) ---[/bold yellow]")
             # Simulate preparing the prompt for an empty message to see base context
             context_data = ai_client.prepare_prompt_for_api(conversation_history, loaded_files, "")
             import json
             console.print(json.dumps(context_data, indent=2))
             console.print("[bold yellow]--- End Context ---[/bold yellow]")
             continue
        elif command == "/help":
             # Re-print help info
             console.print("\nAvailable commands:")
             console.print("  /load <path>... : Load or reload file(s) into context.")
             console.print("  /drop <path>... : Remove file(s) from context.")
             console.print("  /files          : List currently loaded files.")
             console.print("  /clear          : Clear conversation history and loaded files.")
             console.print("  /context        : Show the current context being sent to the AI.")
             console.print("  /help           : Show this help message again.")
             console.print("  /quit or /exit  : Exit the assistant.")
             continue
        elif not user_input.strip(): # Ignore empty input
            continue

        # --- If not a command, process as a message to the AI ---
        process_user_message(user_input)
        # --- End Core Interaction ---

    console.print("[bold cyan]Exiting proCoder. Goodbye![/bold cyan]")

# --- Entry points ---

def run():
    """Function to be called by the entry point script."""
    app()

# Allows running with `python -m proCoder`
if __name__ == "__main__":
    run()