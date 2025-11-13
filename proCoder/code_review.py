"""Code review functionality for reviewing diffs, commits, and PRs."""

import subprocess
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from . import git_utils

console = Console()


class CodeReviewer:
    """Handles code review operations."""

    def __init__(self, repo_root: str):
        """
        Initialize the code reviewer.

        Args:
            repo_root: Root directory of the git repository
        """
        self.repo_root = repo_root

    def review_uncommitted_changes(self) -> Optional[Dict[str, Any]]:
        """
        Review all uncommitted changes (staged and unstaged).

        Returns:
            Dict containing review data
        """
        console.print("[bold cyan]Reviewing uncommitted changes...[/bold cyan]\n")

        # Get staged diff
        staged_result = git_utils._run_git_command(
            ['diff', '--cached', '--no-color'],
            cwd=self.repo_root
        )
        staged_diff = staged_result.stdout if staged_result else ""

        # Get unstaged diff
        unstaged_result = git_utils._run_git_command(
            ['diff', '--no-color'],
            cwd=self.repo_root
        )
        unstaged_diff = unstaged_result.stdout if unstaged_result else ""

        # Get untracked files
        untracked_result = git_utils._run_git_command(
            ['ls-files', '--others', '--exclude-standard'],
            cwd=self.repo_root
        )
        untracked_files = untracked_result.stdout.splitlines() if untracked_result else []

        if not staged_diff and not unstaged_diff and not untracked_files:
            console.print("[yellow]No uncommitted changes found.[/yellow]")
            return None

        review_data = {
            "type": "uncommitted",
            "staged_diff": staged_diff,
            "unstaged_diff": unstaged_diff,
            "untracked_files": untracked_files,
            "summary": self._generate_diff_summary(staged_diff, unstaged_diff, untracked_files)
        }

        self._display_diff_summary(review_data)
        return review_data

    def review_commit(self, commit_ref: str = "HEAD") -> Optional[Dict[str, Any]]:
        """
        Review a specific commit.

        Args:
            commit_ref: Git commit reference (SHA, HEAD, HEAD~1, etc.)

        Returns:
            Dict containing review data
        """
        console.print(f"[bold cyan]Reviewing commit: {commit_ref}[/bold cyan]\n")

        # Get commit information
        commit_info_result = git_utils._run_git_command(
            ['show', '--no-patch', '--format=medium', commit_ref],
            cwd=self.repo_root
        )

        if not commit_info_result:
            console.print(f"[red]Could not find commit:[/red] {commit_ref}")
            return None

        commit_info = commit_info_result.stdout

        # Get commit diff
        diff_result = git_utils._run_git_command(
            ['show', '--no-color', commit_ref],
            cwd=self.repo_root
        )
        diff_content = diff_result.stdout if diff_result else ""

        # Get commit stats
        stats_result = git_utils._run_git_command(
            ['show', '--stat', '--no-color', commit_ref],
            cwd=self.repo_root
        )
        stats = stats_result.stdout if stats_result else ""

        review_data = {
            "type": "commit",
            "commit_ref": commit_ref,
            "commit_info": commit_info,
            "diff": diff_content,
            "stats": stats
        }

        self._display_commit_review(review_data)
        return review_data

    def review_branch_diff(self, base_branch: str = "main", compare_branch: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Review differences between current branch and base branch.

        Args:
            base_branch: Base branch to compare against
            compare_branch: Branch to compare (None = current branch)

        Returns:
            Dict containing review data
        """
        if compare_branch is None:
            compare_branch = git_utils.get_current_branch(self.repo_root)
            if not compare_branch:
                console.print("[red]Could not determine current branch[/red]")
                return None

        console.print(f"[bold cyan]Reviewing changes: {base_branch}...{compare_branch}[/bold cyan]\n")

        # Find merge base
        merge_base_result = git_utils._run_git_command(
            ['merge-base', base_branch, compare_branch],
            cwd=self.repo_root,
            check=False
        )

        if not merge_base_result or merge_base_result.returncode != 0:
            console.print(f"[yellow]Could not find merge base, comparing directly[/yellow]")
            diff_range = f"{base_branch}...{compare_branch}"
        else:
            merge_base = merge_base_result.stdout.strip()
            diff_range = f"{merge_base}...{compare_branch}"

        # Get diff
        diff_result = git_utils._run_git_command(
            ['diff', '--no-color', diff_range],
            cwd=self.repo_root
        )
        diff_content = diff_result.stdout if diff_result else ""

        # Get stats
        stats_result = git_utils._run_git_command(
            ['diff', '--stat', '--no-color', diff_range],
            cwd=self.repo_root
        )
        stats = stats_result.stdout if stats_result else ""

        # Get commit log
        log_result = git_utils._run_git_command(
            ['log', '--oneline', '--no-color', diff_range],
            cwd=self.repo_root
        )
        commits = log_result.stdout if log_result else ""

        if not diff_content and not commits:
            console.print(f"[yellow]No differences found between {base_branch} and {compare_branch}[/yellow]")
            return None

        review_data = {
            "type": "branch_diff",
            "base_branch": base_branch,
            "compare_branch": compare_branch,
            "diff": diff_content,
            "stats": stats,
            "commits": commits
        }

        self._display_branch_diff_review(review_data)
        return review_data

    def list_recent_commits(self, count: int = 10) -> List[Dict[str, str]]:
        """
        List recent commits for selection.

        Args:
            count: Number of commits to list

        Returns:
            List of commit dictionaries
        """
        result = git_utils._run_git_command(
            ['log', f'-{count}', '--format=%H|%h|%an|%ar|%s', '--no-color'],
            cwd=self.repo_root
        )

        if not result:
            return []

        commits = []
        for line in result.stdout.splitlines():
            parts = line.split('|', 4)
            if len(parts) == 5:
                commits.append({
                    "sha": parts[0],
                    "short_sha": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                    "message": parts[4]
                })

        return commits

    def display_commit_picker(self, count: int = 10) -> Optional[str]:
        """
        Display an interactive commit picker.

        Args:
            count: Number of commits to show

        Returns:
            Selected commit SHA or None
        """
        commits = self.list_recent_commits(count)

        if not commits:
            console.print("[yellow]No commits found[/yellow]")
            return None

        table = Table(title=f"Recent Commits (Select by number)", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("SHA", style="yellow", no_wrap=True)
        table.add_column("Author", style="green")
        table.add_column("Date", style="blue")
        table.add_column("Message", style="white")

        for i, commit in enumerate(commits, 1):
            table.add_row(
                str(i),
                commit["short_sha"],
                commit["author"],
                commit["date"],
                commit["message"][:60] + "..." if len(commit["message"]) > 60 else commit["message"]
            )

        console.print(table)
        console.print()

        try:
            choice = console.input("[cyan]Enter commit number (or press Enter to cancel):[/cyan] ").strip()
            if not choice:
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(commits):
                return commits[idx]["sha"]
            else:
                console.print("[red]Invalid selection[/red]")
                return None
        except ValueError:
            console.print("[red]Invalid input[/red]")
            return None

    def _generate_diff_summary(self, staged_diff: str, unstaged_diff: str, untracked_files: List[str]) -> str:
        """Generate a summary of changes."""
        summary_parts = []

        if staged_diff:
            staged_files = self._count_files_in_diff(staged_diff)
            summary_parts.append(f"{staged_files} staged file(s)")

        if unstaged_diff:
            unstaged_files = self._count_files_in_diff(unstaged_diff)
            summary_parts.append(f"{unstaged_files} unstaged file(s)")

        if untracked_files:
            summary_parts.append(f"{len(untracked_files)} untracked file(s)")

        return ", ".join(summary_parts) if summary_parts else "No changes"

    def _count_files_in_diff(self, diff: str) -> int:
        """Count number of files in a diff."""
        count = 0
        for line in diff.splitlines():
            if line.startswith('diff --git'):
                count += 1
        return count

    def _display_diff_summary(self, review_data: Dict[str, Any]):
        """Display summary of uncommitted changes."""
        console.print(Panel(
            f"[bold]{review_data['summary']}[/bold]",
            title="Uncommitted Changes",
            border_style="cyan"
        ))

        if review_data['staged_diff']:
            console.print("\n[bold green]Staged Changes:[/bold green]")
            console.print(review_data['staged_diff'][:1000])  # Limit display
            if len(review_data['staged_diff']) > 1000:
                console.print("[dim]... (truncated)[/dim]")

        if review_data['unstaged_diff']:
            console.print("\n[bold yellow]Unstaged Changes:[/bold yellow]")
            console.print(review_data['unstaged_diff'][:1000])  # Limit display
            if len(review_data['unstaged_diff']) > 1000:
                console.print("[dim]... (truncated)[/dim]")

        if review_data['untracked_files']:
            console.print("\n[bold red]Untracked Files:[/bold red]")
            for file in review_data['untracked_files'][:20]:  # Limit display
                console.print(f"  {file}")
            if len(review_data['untracked_files']) > 20:
                console.print(f"[dim]  ... and {len(review_data['untracked_files']) - 20} more[/dim]")

    def _display_commit_review(self, review_data: Dict[str, Any]):
        """Display commit review information."""
        console.print(Panel(
            review_data['commit_info'],
            title=f"Commit: {review_data['commit_ref']}",
            border_style="cyan"
        ))

        if review_data['stats']:
            console.print("\n[bold]Changes:[/bold]")
            console.print(review_data['stats'])

    def _display_branch_diff_review(self, review_data: Dict[str, Any]):
        """Display branch diff review information."""
        title = f"{review_data['base_branch']}...{review_data['compare_branch']}"

        info = ""
        if review_data['commits']:
            info += "[bold]Commits:[/bold]\n" + review_data['commits'] + "\n\n"

        if review_data['stats']:
            info += "[bold]Changes:[/bold]\n" + review_data['stats']

        console.print(Panel(info, title=title, border_style="cyan"))

    def generate_review_prompt(self, review_data: Dict[str, Any], focus: Optional[str] = None) -> str:
        """
        Generate a prompt for AI code review.

        Args:
            review_data: Review data from review methods
            focus: Specific focus area (e.g., "security", "performance", "bugs")

        Returns:
            Review prompt for AI
        """
        base_prompt = "Please review the following code changes and provide feedback on:\n"
        base_prompt += "1. Potential bugs or issues\n"
        base_prompt += "2. Code quality and best practices\n"
        base_prompt += "3. Security concerns\n"
        base_prompt += "4. Performance implications\n"
        base_prompt += "5. Suggestions for improvement\n\n"

        if focus:
            base_prompt += f"**Special Focus:** {focus}\n\n"

        if review_data["type"] == "uncommitted":
            base_prompt += "## Uncommitted Changes\n\n"
            if review_data["staged_diff"]:
                base_prompt += "### Staged Changes:\n```diff\n"
                base_prompt += review_data["staged_diff"]
                base_prompt += "\n```\n\n"

            if review_data["unstaged_diff"]:
                base_prompt += "### Unstaged Changes:\n```diff\n"
                base_prompt += review_data["unstaged_diff"]
                base_prompt += "\n```\n\n"

            if review_data["untracked_files"]:
                base_prompt += "### Untracked Files:\n"
                for file in review_data["untracked_files"]:
                    base_prompt += f"- {file}\n"

        elif review_data["type"] == "commit":
            base_prompt += f"## Commit: {review_data['commit_ref']}\n\n"
            base_prompt += "### Commit Info:\n```\n"
            base_prompt += review_data["commit_info"]
            base_prompt += "\n```\n\n"
            base_prompt += "### Changes:\n```diff\n"
            base_prompt += review_data["diff"][:10000]  # Limit size for AI
            base_prompt += "\n```\n"

        elif review_data["type"] == "branch_diff":
            base_prompt += f"## Branch Comparison: {review_data['base_branch']}...{review_data['compare_branch']}\n\n"
            if review_data["commits"]:
                base_prompt += "### Commits:\n```\n"
                base_prompt += review_data["commits"]
                base_prompt += "\n```\n\n"

            base_prompt += "### Diff:\n```diff\n"
            base_prompt += review_data["diff"][:10000]  # Limit size for AI
            base_prompt += "\n```\n"

        return base_prompt
