"""Fuzzy file picker for @-mentions in proCoder."""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class FilePicker:
    """Handles fuzzy file picking functionality."""

    def __init__(self, working_dir: str, git_repo_root: Optional[str] = None):
        """
        Initialize the file picker.

        Args:
            working_dir: Current working directory
            git_repo_root: Git repository root if available
        """
        self.working_dir = working_dir
        self.git_repo_root = git_repo_root or working_dir
        self.file_cache: List[str] = []
        self._refresh_cache()

    def _refresh_cache(self):
        """Refresh the file cache with files from the repository."""
        self.file_cache = []

        # Try to use git ls-files for tracked files
        if self.git_repo_root:
            try:
                from . import git_utils
                tracked_files = git_utils.get_tracked_files(self.git_repo_root)
                self.file_cache = [os.path.relpath(f, self.git_repo_root) for f in tracked_files]
                return
            except Exception:
                pass  # Fall back to directory scanning

        # Fall back to directory scanning
        try:
            for root, dirs, files in os.walk(self.working_dir):
                # Skip common ignore directories
                dirs[:] = [d for d in dirs if d not in {
                    '.git', '.svn', '.hg', 'node_modules', '__pycache__',
                    '.venv', 'venv', '.tox', '.eggs', 'dist', 'build'
                }]

                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.working_dir)
                    self.file_cache.append(rel_path)

        except Exception as e:
            console.print(f"[yellow]Warning: Could not scan directory: {e}[/yellow]")

    def fuzzy_search(self, query: str, max_results: int = 10) -> List[Tuple[str, int]]:
        """
        Perform fuzzy search on file paths.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of (filepath, score) tuples, sorted by score
        """
        if not query:
            return []

        query_lower = query.lower()
        results = []

        for filepath in self.file_cache:
            score = self._calculate_match_score(filepath.lower(), query_lower)
            if score > 0:
                results.append((filepath, score))

        # Sort by score (higher is better)
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:max_results]

    def _calculate_match_score(self, filepath: str, query: str) -> int:
        """
        Calculate fuzzy match score.

        Args:
            filepath: File path to match against
            query: Search query

        Returns:
            Match score (higher is better, 0 = no match)
        """
        score = 0

        # Exact match
        if query in filepath:
            score += 100

        # Filename match is better than path match
        filename = os.path.basename(filepath)
        if query in filename:
            score += 50

        # Bonus for matching at word boundaries
        parts = filepath.split(os.sep)
        for part in parts:
            if part.startswith(query):
                score += 30

        # Bonus for exact filename match
        if filename == query:
            score += 200

        # Bonus for matching file extension
        if '.' in query:
            query_ext = query.split('.')[-1]
            file_ext = filepath.split('.')[-1] if '.' in filepath else ""
            if query_ext == file_ext:
                score += 20

        # Fuzzy character matching
        query_idx = 0
        for char in filepath:
            if query_idx < len(query) and char == query[query_idx]:
                score += 1
                query_idx += 1

        # Only return if we matched all query characters
        if query_idx < len(query):
            return 0

        # Penalty for length (prefer shorter paths)
        score -= len(filepath) // 10

        return max(0, score)

    def interactive_pick(self, initial_query: str = "") -> Optional[str]:
        """
        Interactive file picker with live search.

        Args:
            initial_query: Initial search query

        Returns:
            Selected file path or None
        """
        query = initial_query

        while True:
            # Search for files
            results = self.fuzzy_search(query, max_results=15)

            # Display results
            os.system('clear' if os.name != 'nt' else 'cls')  # Clear screen

            console.print(Panel(
                f"[bold cyan]File Picker[/bold cyan]\n\n"
                f"Query: [yellow]{query}[/yellow]\n"
                f"Results: {len(results)} files\n\n"
                f"[dim]Type to search, Enter to select, Esc to cancel[/dim]",
                border_style="cyan"
            ))

            if results:
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("#", style="dim", width=3)
                table.add_column("File", style="green")
                table.add_column("Path", style="blue")

                for i, (filepath, score) in enumerate(results, 1):
                    filename = os.path.basename(filepath)
                    dirname = os.path.dirname(filepath) or "."
                    table.add_row(str(i), filename, dirname)

                console.print(table)
            else:
                console.print("[yellow]No matching files found[/yellow]")

            # Get user input
            console.print()
            user_input = console.input("[cyan]Search (or number to select):[/cyan] ").strip()

            # Handle input
            if not user_input:  # Empty = continue searching
                continue

            if user_input.isdigit():
                # Select by number
                idx = int(user_input) - 1
                if 0 <= idx < len(results):
                    selected_file = results[idx][0]
                    console.print(f"[green]Selected:[/green] {selected_file}")
                    return os.path.join(self.working_dir, selected_file)
                else:
                    console.print("[red]Invalid selection[/red]")
                    continue

            # Update query
            query = user_input

    def pick_from_query(self, query: str, auto_select: bool = False) -> Optional[str]:
        """
        Pick a file from a query string.

        Args:
            query: Search query
            auto_select: Automatically select if only one match

        Returns:
            Selected file path or None
        """
        results = self.fuzzy_search(query, max_results=10)

        if not results:
            console.print(f"[yellow]No files found matching:[/yellow] {query}")
            return None

        if len(results) == 1 and auto_select:
            # Auto-select single match
            selected_file = results[0][0]
            console.print(f"[green]Auto-selected:[/green] {selected_file}")
            return os.path.join(self.working_dir, selected_file)

        # Display results for selection
        table = Table(title=f"Files matching: {query}", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("File", style="green")
        table.add_column("Path", style="blue")
        table.add_column("Score", justify="right", style="yellow")

        for i, (filepath, score) in enumerate(results, 1):
            filename = os.path.basename(filepath)
            dirname = os.path.dirname(filepath) or "."
            table.add_row(str(i), filename, dirname, str(score))

        console.print(table)

        # Get user selection
        try:
            choice = console.input("[cyan]Select file number (or Enter to cancel):[/cyan] ").strip()
            if not choice:
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(results):
                selected_file = results[idx][0]
                console.print(f"[green]Selected:[/green] {selected_file}")
                return os.path.join(self.working_dir, selected_file)
            else:
                console.print("[red]Invalid selection[/red]")
                return None

        except ValueError:
            console.print("[red]Invalid input[/red]")
            return None

    def extract_at_mentions(self, text: str) -> List[str]:
        """
        Extract @file mentions from text.

        Args:
            text: Text containing @mentions

        Returns:
            List of file paths mentioned
        """
        import re

        # Match @filename or @path/to/file
        pattern = r'@([a-zA-Z0-9_\-./]+)'
        matches = re.findall(pattern, text)

        file_paths = []
        for match in matches:
            # Try to find matching file
            if os.path.exists(match):
                file_paths.append(match)
            else:
                # Try fuzzy search
                results = self.fuzzy_search(match, max_results=1)
                if results:
                    file_paths.append(results[0][0])

        return file_paths

    def replace_at_mentions(self, text: str) -> Tuple[str, List[str]]:
        """
        Replace @mentions with actual file paths.

        Args:
            text: Text containing @mentions

        Returns:
            Tuple of (processed text, list of file paths)
        """
        import re

        file_paths = []
        processed_text = text

        # Find all @mentions
        pattern = r'@([a-zA-Z0-9_\-./]+)'
        matches = re.finditer(pattern, text)

        for match in matches:
            mention = match.group(1)
            # Try fuzzy search
            results = self.fuzzy_search(mention, max_results=1)

            if results:
                filepath = results[0][0]
                file_paths.append(filepath)
                # Replace @mention with actual path
                processed_text = processed_text.replace(f'@{mention}', filepath)

        return processed_text, file_paths

    def refresh(self):
        """Refresh the file cache."""
        console.print("[blue]Refreshing file cache...[/blue]")
        self._refresh_cache()
        console.print(f"[green]Found {len(self.file_cache)} files[/green]")
