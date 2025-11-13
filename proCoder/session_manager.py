"""Session manager for storing and resuming conversations."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import hashlib

console = Console()


class SessionManager:
    """Manages conversation sessions for resume functionality."""

    def __init__(self, sessions_dir: Optional[str] = None):
        """
        Initialize the session manager.

        Args:
            sessions_dir: Directory to store session files (default: ~/.procoder/sessions)
        """
        if sessions_dir is None:
            home = Path.home()
            sessions_dir = home / ".procoder" / "sessions"

        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.current_session_data: Dict[str, Any] = {}

    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().isoformat()
        random_hash = hashlib.md5(f"{timestamp}{os.getpid()}".encode()).hexdigest()[:12]
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random_hash}"

    def create_session(self, working_dir: str, loaded_files: Dict[str, str],
                       git_repo_root: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """
        Create a new session.

        Args:
            working_dir: Current working directory
            loaded_files: Dictionary of loaded files {path: content}
            git_repo_root: Git repository root if in a repo
            metadata: Additional metadata to store

        Returns:
            Session ID
        """
        session_id = self.generate_session_id()
        self.current_session_id = session_id

        self.current_session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "working_dir": working_dir,
            "git_repo_root": git_repo_root,
            "loaded_files": list(loaded_files.keys()),  # Store paths, not content
            "conversation_history": [],
            "metadata": metadata or {},
            "model_history": [],
            "file_changes": []
        }

        self._save_session()
        console.print(f"[green]Created session:[/green] {session_id}")
        return session_id

    def update_session(self, conversation_history: List[Dict],
                       loaded_files: Dict[str, str],
                       model_name: Optional[str] = None,
                       file_changes: Optional[List[Dict]] = None):
        """
        Update the current session with new data.

        Args:
            conversation_history: Current conversation history
            loaded_files: Currently loaded files
            model_name: Current model name
            file_changes: List of file changes made
        """
        if not self.current_session_id:
            console.print("[yellow]Warning: No active session to update[/yellow]")
            return

        self.current_session_data["conversation_history"] = conversation_history
        self.current_session_data["loaded_files"] = list(loaded_files.keys())
        self.current_session_data["updated_at"] = datetime.now().isoformat()

        if model_name and (not self.current_session_data["model_history"] or
                          self.current_session_data["model_history"][-1] != model_name):
            self.current_session_data["model_history"].append(model_name)

        if file_changes:
            self.current_session_data["file_changes"].extend(file_changes)

        self._save_session()

    def _save_session(self):
        """Save the current session to disk."""
        if not self.current_session_id:
            return

        session_file = self.sessions_dir / f"{self.current_session_id}.json"

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_session_data, f, indent=2, ensure_ascii=False)

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a session by ID.

        Args:
            session_id: Session ID to load

        Returns:
            Session data or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            console.print(f"[red]Session not found:[/red] {session_id}")
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                self.current_session_data = json.load(f)
                self.current_session_id = session_id
                console.print(f"[green]Loaded session:[/green] {session_id}")
                return self.current_session_data
        except Exception as e:
            console.print(f"[red]Error loading session:[/red] {e}")
            return None

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        sessions = []

        for session_file in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            if len(sessions) >= limit:
                break

            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Create summary
                    summary = {
                        "session_id": data.get("session_id"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "working_dir": data.get("working_dir"),
                        "git_repo_root": data.get("git_repo_root"),
                        "num_messages": len(data.get("conversation_history", [])),
                        "num_files": len(data.get("loaded_files", [])),
                        "models_used": data.get("model_history", []),
                        "num_changes": len(data.get("file_changes", []))
                    }
                    sessions.append(summary)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {session_file.name}: {e}[/yellow]")
                continue

        return sessions

    def display_recent_sessions(self, limit: int = 10):
        """Display a table of recent sessions."""
        sessions = self.get_recent_sessions(limit)

        if not sessions:
            console.print("[yellow]No sessions found[/yellow]")
            return

        table = Table(title="Recent Sessions", show_header=True, header_style="bold cyan")
        table.add_column("Session ID", style="green", no_wrap=True)
        table.add_column("Created", style="blue")
        table.add_column("Updated", style="blue")
        table.add_column("Messages", justify="right")
        table.add_column("Files", justify="right")
        table.add_column("Changes", justify="right")
        table.add_column("Working Dir", style="dim")

        for session in sessions:
            created = datetime.fromisoformat(session["created_at"]).strftime("%Y-%m-%d %H:%M")
            updated = datetime.fromisoformat(session["updated_at"]).strftime("%Y-%m-%d %H:%M")
            work_dir = Path(session["working_dir"]).name if session.get("working_dir") else "-"

            table.add_row(
                session["session_id"],
                created,
                updated,
                str(session["num_messages"]),
                str(session["num_files"]),
                str(session["num_changes"]),
                work_dir
            )

        console.print(table)

    def display_session_summary(self, session_id: Optional[str] = None):
        """Display a summary of a session."""
        if session_id:
            session_data = self.load_session(session_id)
        else:
            session_data = self.current_session_data

        if not session_data:
            console.print("[yellow]No session data available[/yellow]")
            return

        summary_text = f"""
[bold cyan]Session ID:[/bold cyan] {session_data.get('session_id', 'N/A')}
[bold cyan]Created:[/bold cyan] {session_data.get('created_at', 'N/A')}
[bold cyan]Updated:[/bold cyan] {session_data.get('updated_at', 'N/A')}
[bold cyan]Working Directory:[/bold cyan] {session_data.get('working_dir', 'N/A')}
[bold cyan]Git Repository:[/bold cyan] {session_data.get('git_repo_root', 'None')}
[bold cyan]Messages:[/bold cyan] {len(session_data.get('conversation_history', []))}
[bold cyan]Loaded Files:[/bold cyan] {len(session_data.get('loaded_files', []))}
[bold cyan]File Changes:[/bold cyan] {len(session_data.get('file_changes', []))}
[bold cyan]Models Used:[/bold cyan] {', '.join(session_data.get('model_history', [])) or 'None'}
"""

        console.print(Panel(summary_text, title="Session Summary", border_style="cyan"))

        if session_data.get('loaded_files'):
            console.print("\n[bold cyan]Loaded Files:[/bold cyan]")
            for i, filepath in enumerate(session_data['loaded_files'], 1):
                console.print(f"  {i}. {filepath}")

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted successfully
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            console.print(f"[red]Session not found:[/red] {session_id}")
            return False

        try:
            session_file.unlink()
            console.print(f"[green]Deleted session:[/green] {session_id}")

            if self.current_session_id == session_id:
                self.current_session_id = None
                self.current_session_data = {}

            return True
        except Exception as e:
            console.print(f"[red]Error deleting session:[/red] {e}")
            return False

    def cleanup_old_sessions(self, keep_count: int = 50):
        """
        Remove old sessions, keeping only the most recent ones.

        Args:
            keep_count: Number of sessions to keep
        """
        session_files = sorted(self.sessions_dir.glob("*.json"), reverse=True)

        if len(session_files) <= keep_count:
            console.print(f"[blue]No cleanup needed. Found {len(session_files)} sessions.[/blue]")
            return

        files_to_delete = session_files[keep_count:]
        deleted_count = 0

        for session_file in files_to_delete:
            try:
                session_file.unlink()
                deleted_count += 1
            except Exception as e:
                console.print(f"[yellow]Warning: Could not delete {session_file.name}: {e}[/yellow]")

        console.print(f"[green]Cleaned up {deleted_count} old sessions (kept {keep_count} most recent)[/green]")

    def get_last_session_id(self) -> Optional[str]:
        """Get the ID of the most recent session."""
        sessions = self.get_recent_sessions(limit=1)
        return sessions[0]["session_id"] if sessions else None

    def export_session(self, session_id: str, output_path: str) -> bool:
        """
        Export a session to a file.

        Args:
            session_id: Session ID to export
            output_path: Path to save the exported session

        Returns:
            True if exported successfully
        """
        session_data = self.load_session(session_id)

        if not session_data:
            return False

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            console.print(f"[green]Exported session to:[/green] {output_path}")
            return True
        except Exception as e:
            console.print(f"[red]Error exporting session:[/red] {e}")
            return False

    def import_session(self, import_path: str) -> Optional[str]:
        """
        Import a session from a file.

        Args:
            import_path: Path to the session file to import

        Returns:
            Session ID if imported successfully
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Generate new session ID for import
            new_id = self.generate_session_id()
            session_data["session_id"] = new_id
            session_data["imported_at"] = datetime.now().isoformat()

            self.current_session_id = new_id
            self.current_session_data = session_data
            self._save_session()

            console.print(f"[green]Imported session as:[/green] {new_id}")
            return new_id
        except Exception as e:
            console.print(f"[red]Error importing session:[/red] {e}")
            return None
