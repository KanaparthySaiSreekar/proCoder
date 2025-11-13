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
from . import search_utils
from . import model_manager
from . import memory_system
from . import openrouter_integration
from . import ascii_art
from . import session_manager
from . import approval_modes
from . import code_review
from . import web_search
from . import slash_commands
from . import file_picker

# --- Setup ---
app = typer.Typer(help="proCoder: AI assistant for code editing in your terminal.")
console = Console()

# --- Global State (Consider using a State Class for larger applications) ---
conversation_history = []
# Store absolute paths for consistency
loaded_files: dict[str, str] = {} # {absolute_filepath: content}
git_repo_root: Optional[str] = None # Store root path if detected
# Model manager for dynamic model switching
model_mgr: Optional[model_manager.ModelManager] = None
# Memory system for persistent context
memory: Optional[memory_system.MemorySystem] = None
# Session manager for resume functionality
session_mgr: Optional[session_manager.SessionManager] = None
# Approval manager for permission control
approval_mgr: Optional[approval_modes.ApprovalManager] = None
# Code reviewer for diff/commit review
code_reviewer: Optional[code_review.CodeReviewer] = None
# Web searcher for web search capability
web_searcher: Optional[web_search.WebSearcher] = None
# Slash command manager
slash_cmd_mgr: Optional[slash_commands.SlashCommandManager] = None
# File picker for fuzzy file search
file_picker_mgr: Optional[file_picker.FilePicker] = None

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
    """Adds system prompts, Git context, memory, and loaded file content."""
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
        "5. If the user's request is unclear, ask clarifying questions.\n"
        "6. Pay attention to the project memory and user preferences provided below."
    )
    conversation_history.append({"role": "system", "content": system_prompt})

    # 2. Git Context (if in a repo)
    if git_repo_root:
        git_context = f"The user is working inside a Git repository located at: {git_repo_root}\n"
        # Optional: Add branch name, recent commits, etc.
        # branch_process = git_utils._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=git_repo_root)
        # if branch_process: git_context += f"Current branch: {branch_process.stdout.strip()}\n"
        conversation_history.append({"role": "system", "content": git_context.strip()})

    # 3. Memory Context (persistent knowledge)
    if memory:
        memory_summary = memory.get_context_summary()
        if memory_summary:
            memory_context = "# Project Memory\n\n" + memory_summary
            conversation_history.append({"role": "system", "content": memory_context})
            console.print("[dim]Added project memory to context.[/dim]")

    # 4. File Context
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
    current_model = model_mgr.get_current_model_name() if model_mgr else config.MODEL_NAME
    console.print(f"[bold blue]AI ({current_model}):[/bold blue]", end="")
    try:
        with Live(console=console, refresh_per_second=10, vertical_overflow="visible") as live:
            accumulated_response_markdown = ""
            active_model = model_mgr.get_current_model_id() if model_mgr else config.MODEL_NAME
            for chunk in ai_client.stream_ai_response(prompt_data, active_model):
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
    extracted_changes, new_files = utils.extract_code_changes(full_response, list(loaded_files.keys()))

    all_modified_paths = []

    # Handle changes to existing files
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

                all_modified_paths.extend(updated_abs_paths)
            else:
                console.print("\n[yellow]No changes were ultimately applied to files.[/yellow]")

    # Handle new file creation
    if new_files:
        approved_new_files = utils.prompt_for_new_files(new_files, git_repo_root)

        if approved_new_files:
            # Resolve paths relative to repo root if available
            resolved_new_files = {}
            for filename, content in approved_new_files.items():
                if git_repo_root and not os.path.isabs(filename):
                    # Make path relative to repo root
                    resolved_path = os.path.join(git_repo_root, filename)
                else:
                    # Use as absolute path or relative to CWD
                    resolved_path = os.path.abspath(filename)
                resolved_new_files[resolved_path] = content

            created_abs_paths = file_manager.apply_new_files(resolved_new_files)

            if created_abs_paths:
                console.print(f"\n[green]Successfully created {len(created_abs_paths)} new file(s).[/green]")
                # Load new files into context
                console.print("[blue]Loading new files into context...[/blue]")
                for abs_path in created_abs_paths:
                    load_file_content(abs_path)

                all_modified_paths.extend(created_abs_paths)
            else:
                console.print("\n[yellow]No new files were created.[/yellow]")

    # --- Git Integration ---
    if git_repo_root and all_modified_paths:
        handle_git_operations(all_modified_paths)

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
    # Skip initialization for setup/login commands (they don't need API key)
    if ctx.invoked_subcommand in ['setup', 'login']:
        return

    global git_repo_root, model_mgr, memory, session_mgr, approval_mgr
    global code_reviewer, web_searcher, slash_cmd_mgr, file_picker_mgr

    # Detect Git repo based on CWD *before* processing files
    git_repo_root = git_utils.get_repo_root()
    if git_repo_root:
        console.print(f"[dim]Detected Git repository root: {git_repo_root}[/dim]")
    else:
        console.print("[dim]Not inside a Git repository.[/dim]")

    # Initialize model manager
    default_model_key = "gemini-flash"
    # Try to map config.MODEL_NAME to a model key
    for key, model_info in model_manager.AVAILABLE_MODELS.items():
        if config.MODEL_NAME and config.MODEL_NAME.lower() in model_info["id"].lower():
            default_model_key = key
            break
    model_mgr = model_manager.initialize_model_manager(default_model_key)

    # Initialize memory system
    memory = memory_system.initialize_memory_system(git_repo_root)

    # Initialize session manager
    session_mgr = session_manager.SessionManager()

    # Initialize approval manager
    working_dir = git_repo_root if git_repo_root else os.getcwd()
    approval_mgr = approval_modes.ApprovalManager(
        initial_mode=approval_modes.ApprovalMode.AUTO,
        working_dir=working_dir
    )

    # Initialize code reviewer (if in git repo)
    if git_repo_root:
        code_reviewer = code_review.CodeReviewer(git_repo_root)

    # Initialize web searcher (disabled by default)
    web_enabled = config.get_bool_env("WEB_SEARCH_ENABLED", False)
    web_searcher = web_search.WebSearcher(enabled=web_enabled)

    # Initialize slash commands manager
    slash_cmd_mgr = slash_commands.SlashCommandManager()

    # Initialize file picker
    file_picker_mgr = file_picker.FilePicker(working_dir, git_repo_root)


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
    # Check if API key is configured
    if not config.require_api_key():
        return

    global loaded_files
    global git_repo_root

    # Display beautiful welcome screen
    from rich.text import Text
    from rich.align import Align

    # Create gradient logo
    logo_text = Text(ascii_art.LOGO, style="bold cyan")
    tagline = Text("AI-Powered Coding Assistant", style="italic bright_magenta")
    version = Text(f"v0.5.0  {ascii_art.LIGHTNING} Session Resume  {ascii_art.BRAIN} Code Review  {ascii_art.ROCKET} Git Workflow", style="dim cyan")

    console.print()
    console.print(Align.center(logo_text))
    console.print(Align.center(tagline))
    console.print(Align.center(version))
    console.print()
    console.print(Panel(
        "[cyan]Professional coding assistant with 12+ AI models at your fingertips[/cyan]",
        border_style="bright_blue",
        padding=(0, 2)
    ))
    console.print()

    initial_load_success = True
    if files:
        console.print(f"[cyan]{ascii_art.PACKAGE} Loading initial files...[/cyan]")
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

    # Display commands in a beautiful format
    from rich.table import Table

    console.print()
    commands_table = Table(title="[bold cyan]Available Commands[/bold cyan]", border_style="bright_blue", show_header=True, header_style="bold magenta")
    commands_table.add_column("Command", style="cyan", no_wrap=True)
    commands_table.add_column("Description", style="white")

    # File operations
    commands_table.add_row("[yellow]/load[/yellow] <path>...", "Load or reload file(s) into context")
    commands_table.add_row("[yellow]/drop[/yellow] <path>...", "Remove file(s) from context")
    commands_table.add_row("[yellow]/files[/yellow]", "List currently loaded files")

    # AI & Models
    commands_table.add_row("[green]/model[/green] [name|list|back]", f"{ascii_art.BRAIN} Switch AI model or list available models")
    commands_table.add_row("[green]/or[/green] [account|models|help]", f"{ascii_art.ROCKET} OpenRouter account & model management")

    # Memory
    commands_table.add_row("[magenta]/remember[/magenta] [show|fact|pref]", f"{ascii_art.SPARKLE} Manage persistent project memory")

    # Code search
    commands_table.add_row("[blue]/search[/blue] <pattern> [files]", "Search for pattern in files (regex)")
    commands_table.add_row("[blue]/find[/blue] <identifier> [files]", "Find definitions of functions/classes")

    # History
    commands_table.add_row("[red]/undo[/red]", "Undo the last file change")
    commands_table.add_row("[red]/redo[/red]", "Redo the last undone change")
    commands_table.add_row("[red]/history[/red]", "Show change history")

    # Utility
    commands_table.add_row("/clear", "Clear conversation history")
    commands_table.add_row("/context", "Show the current context being sent to the AI")
    commands_table.add_row("/help", "Show this help message again")
    commands_table.add_row("/quit or /exit", "Exit the assistant")

    console.print(commands_table)
    console.print()

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
        elif command.startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 1 or parts[1] == "list":
                # Show available models
                model_mgr.list_models()
            elif parts[1] == "back":
                # Switch to previous model
                model_mgr.previous_model()
            elif parts[1] == "info":
                # Show current model info
                info = model_mgr.get_model_info()
                console.print(f"\n[bold cyan]Current Model: {info['name']}[/bold cyan]")
                console.print(f"  ID: {info['id']}")
                console.print(f"  Speed: {info['speed']}")
                console.print(f"  Cost: {info['cost']}")
                console.print(f"  Context Window: {info['context']}")
                console.print(f"  Best For: {info['best_for']}")
            else:
                # Try to switch to specified model
                model_mgr.switch_model(parts[1])
            continue
        elif command.startswith("/remember"):
            parts = user_input.split(maxsplit=2)
            subcommand = parts[1] if len(parts) > 1 else "show"

            if subcommand == "show":
                section = parts[2] if len(parts) > 2 else None
                memory.display_memory(section)
            elif subcommand == "fact":
                if len(parts) < 3:
                    console.print("[yellow]Usage: /remember fact <key>=<value> [category][/yellow]")
                    console.print("Example: /remember fact framework=FastAPI technology")
                else:
                    fact_parts = parts[2].split('=', 1)
                    if len(fact_parts) == 2:
                        key, value = fact_parts
                        category = parts[3] if len(parts) > 3 else "general"
                        memory.add_fact(key.strip(), value.strip(), category)
                    else:
                        console.print("[yellow]Invalid format. Use key=value[/yellow]")
            elif subcommand == "pref":
                if len(parts) < 3:
                    console.print("[yellow]Usage: /remember pref <key>=<value>[/yellow]")
                    console.print("Example: /remember pref indent=4")
                else:
                    pref_parts = parts[2].split('=', 1)
                    if len(pref_parts) == 2:
                        key, value = pref_parts
                        memory.set_preference(key.strip(), value.strip())
                    else:
                        console.print("[yellow]Invalid format. Use key=value[/yellow]")
            elif subcommand == "pattern":
                if len(parts) < 3:
                    console.print("[yellow]Usage: /remember pattern <description>[/yellow]")
                else:
                    memory.add_pattern(parts[2])
            elif subcommand == "arch":
                if len(parts) < 3:
                    console.print("[yellow]Usage: /remember arch <component> <description>[/yellow]")
                else:
                    component_desc = parts[2].split(' ', 1)
                    if len(component_desc) == 2:
                        memory.add_architecture_note(component_desc[0], component_desc[1])
                    else:
                        console.print("[yellow]Provide both component name and description[/yellow]")
            elif subcommand == "clear":
                section = parts[2] if len(parts) > 2 else None
                if section:
                    memory.clear_section(section)
                else:
                    console.print("[yellow]Specify section to clear: facts, preferences, patterns, architecture, todos, changes[/yellow]")
            else:
                console.print("[yellow]Unknown subcommand. Use: show, fact, pref, pattern, arch, clear[/yellow]")
            continue
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
        elif command.startswith("/search"):
            parts = user_input.split(maxsplit=2)
            if len(parts) < 2:
                console.print("[yellow]Usage: /search <pattern> [file_pattern][/yellow]")
                console.print("Example: /search 'def main' *.py")
                continue

            search_pattern = parts[1]
            file_pattern = parts[2] if len(parts) > 2 else "*"

            search_dir = git_repo_root if git_repo_root else os.getcwd()
            console.print(f"[blue]Searching for '{search_pattern}' in {search_dir}...[/blue]")

            results = search_utils.search_in_directory(
                search_dir,
                search_pattern,
                file_pattern,
                case_sensitive=True,
                context_lines=2
            )

            search_utils.display_search_results(results, search_pattern)
            continue

        elif command.startswith("/find"):
            parts = user_input.split(maxsplit=2)
            if len(parts) < 2:
                console.print("[yellow]Usage: /find <identifier> [file_pattern][/yellow]")
                console.print("Example: /find MyClass *.py")
                continue

            identifier = parts[1]
            file_pattern = parts[2] if len(parts) > 2 else "*.py"

            search_dir = git_repo_root if git_repo_root else os.getcwd()
            console.print(f"[blue]Finding definitions of '{identifier}' in {search_dir}...[/blue]")

            results = search_utils.find_definition(search_dir, identifier, file_pattern)

            if not results:
                console.print(f"[yellow]No definitions found for:[/yellow] {identifier}")
            else:
                console.print(f"[green]Found {sum(len(matches) for matches in results.values())} definition(s):[/green]\n")
                for filepath, matches in sorted(results.items()):
                    console.print(f"[bold magenta]{filepath}[/bold magenta]")
                    for line_num, line_text in matches:
                        console.print(f"  [cyan]Line {line_num}:[/cyan] {line_text.strip()}")
            continue

        elif command == "/undo":
            if file_manager.undo():
                # Reload affected files if they're in context
                console.print("[blue]Reloading affected files...[/blue]")
                for abs_path in list(loaded_files.keys()):
                    if os.path.exists(abs_path):
                        load_file_content(abs_path)
            continue

        elif command == "/redo":
            if file_manager.redo():
                # Reload affected files if they're in context
                console.print("[blue]Reloading affected files...[/blue]")
                for abs_path in list(loaded_files.keys()):
                    if os.path.exists(abs_path):
                        load_file_content(abs_path)
            continue

        elif command == "/history":
            history_info = file_manager.get_history_info()
            console.print(history_info)
            continue

        elif command.startswith("/openrouter") or command.startswith("/or"):
            parts = user_input.split(maxsplit=1)
            subcommand = parts[1] if len(parts) > 1 else "account"

            if subcommand == "account" or subcommand == "info":
                # Show account dashboard
                or_client = openrouter_integration.get_openrouter_client()
                if not or_client:
                    or_client = openrouter_integration.initialize_openrouter_client(config.API_KEY)
                or_client.display_account_dashboard()
            elif subcommand == "models" or subcommand.startswith("browse"):
                # Browse available models
                or_client = openrouter_integration.get_openrouter_client()
                if not or_client:
                    or_client = openrouter_integration.initialize_openrouter_client(config.API_KEY)

                category = parts[1].split(maxsplit=1)[1] if len(parts) > 1 and ' ' in parts[1] else None
                or_client.display_model_browser(category)
            elif subcommand == "validate":
                # Validate current API key
                or_client = openrouter_integration.OpenRouterClient(config.API_KEY)
                if or_client.validate_api_key():
                    console.print("[green]✓ API key is valid![/green]")
                    or_client.display_account_dashboard()
                else:
                    console.print("[red]✗ API key is invalid or expired.[/red]")
                    console.print("[yellow]Run 'proCoder setup' to configure a new key.[/yellow]")
            elif subcommand == "help":
                console.print("\n[bold cyan]OpenRouter Commands:[/bold cyan]")
                console.print("  /or account     : View account info and usage")
                console.print("  /or models      : Browse all available models")
                console.print("  /or browse <provider> : Browse models from specific provider")
                console.print("  /or validate    : Validate your API key")
                console.print("\n[dim]Full setup commands:[/dim]")
                console.print("  proCoder setup  : Interactive setup wizard")
                console.print("  proCoder login  : Quick login for existing users")
                console.print("  proCoder models : Browse models from CLI")
                console.print("  proCoder account: View account info from CLI")
            else:
                console.print(f"[yellow]Unknown OpenRouter subcommand: {subcommand}[/yellow]")
                console.print("[dim]Use /or help to see available commands[/dim]")
            continue

        elif command == "/help":
             # Re-print help info
             console.print("\nAvailable commands:")
             console.print("  /load <path>...            : Load or reload file(s) into context.")
             console.print("  /drop <path>...            : Remove file(s) from context.")
             console.print("  /files                     : List currently loaded files.")
             console.print("  /model [name|list|back]    : Switch AI model or list available models.")
             console.print("  /or [account|models|help]  : OpenRouter account & model management.")
             console.print("  /remember [show|fact|pref] : Manage persistent project memory.")
             console.print("  /search <pattern> [files]  : Search for pattern in files (regex supported).")
             console.print("  /find <identifier> [files] : Find definitions of functions/classes.")
             console.print("  /undo                      : Undo the last file change.")
             console.print("  /redo                      : Redo the last undone change.")
             console.print("  /history                   : Show change history.")
             console.print("  /clear                     : Clear conversation history and loaded files.")
             console.print("  /context                   : Show the current context being sent to the AI.")
             console.print("  /help                      : Show this help message again.")
             console.print("  /quit or /exit             : Exit the assistant.")
             continue
        elif not user_input.strip(): # Ignore empty input
            continue

        # --- If not a command, process as a message to the AI ---
        process_user_message(user_input)
        # --- End Core Interaction ---

    console.print("[bold cyan]Exiting proCoder. Goodbye![/bold cyan]")


@app.command()
def setup():
    """
    Interactive setup wizard for first-time configuration.
    Guides you through getting and configuring your OpenRouter API key.
    """
    console.print(Panel("[bold magenta]proCoder Setup Wizard[/bold magenta]", expand=False))
    api_key = openrouter_integration.setup_wizard()

    if api_key:
        console.print("\n[bold green]✓ Setup complete![/bold green]")
        console.print("[dim]You can now run: proCoder main[/dim]")
    else:
        console.print("\n[yellow]Setup incomplete. You can run 'proCoder setup' again later.[/yellow]")


@app.command()
def login():
    """
    Quick login for existing OpenRouter users.
    Enter your API key to authenticate.
    """
    api_key = openrouter_integration.quick_login()

    if api_key:
        console.print("\n[green]✓ Login successful![/green]")
    else:
        console.print("\n[yellow]Login cancelled.[/yellow]")


@app.command()
def models(
    category: Annotated[Optional[str], typer.Argument(help="Filter by provider (e.g., 'anthropic', 'openai')")] = None
):
    """
    Browse all available models on OpenRouter.
    Displays models with pricing, context limits, and descriptions.
    """
    # Check if API key is configured
    if not config.require_api_key():
        return

    try:
        client = openrouter_integration.OpenRouterClient(config.API_KEY)
        client.display_model_browser(category)
    except Exception as e:
        console.print(f"[red]Error browsing models:[/red] {e}")


@app.command()
def account():
    """
    View your OpenRouter account information.
    Shows usage statistics, credits, and rate limits.
    """
    # Check if API key is configured
    if not config.require_api_key():
        return

    try:
        client = openrouter_integration.OpenRouterClient(config.API_KEY)
        client.display_account_dashboard()
    except Exception as e:
        console.print(f"[red]Error fetching account info:[/red] {e}")


# --- Entry points ---

def run():
    """Function to be called by the entry point script."""
    app()

# Allows running with `python -m proCoder`
if __name__ == "__main__":
    run()