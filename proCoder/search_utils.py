"""
Utilities for searching code in the project.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

def search_in_file(filepath: str, pattern: str, case_sensitive: bool = True, context_lines: int = 2) -> List[Tuple[int, str, List[str]]]:
    """
    Search for a pattern in a file and return matching lines with context.

    Args:
        filepath: Path to the file to search
        pattern: Regular expression pattern to search for
        case_sensitive: Whether the search should be case-sensitive
        context_lines: Number of lines of context to show around matches

    Returns:
        List of tuples (line_number, matching_line, context_lines)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception:
            return []
    except Exception:
        return []

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        console.print(f"[red]Invalid regex pattern:[/red] {e}")
        return []

    matches = []
    for i, line in enumerate(lines):
        if regex.search(line):
            # Get context lines
            start_ctx = max(0, i - context_lines)
            end_ctx = min(len(lines), i + context_lines + 1)
            context = lines[start_ctx:end_ctx]
            matches.append((i + 1, line.rstrip(), context))

    return matches


def search_in_directory(
    directory: str,
    pattern: str,
    file_pattern: str = "*",
    case_sensitive: bool = True,
    context_lines: int = 2,
    exclude_dirs: Optional[List[str]] = None
) -> Dict[str, List[Tuple[int, str, List[str]]]]:
    """
    Search for a pattern recursively in a directory.

    Args:
        directory: Root directory to search
        pattern: Regular expression pattern to search for
        file_pattern: Glob pattern for files to include (e.g., "*.py")
        case_sensitive: Whether the search should be case-sensitive
        context_lines: Number of lines of context to show around matches
        exclude_dirs: List of directory names to exclude (e.g., ['.git', 'node_modules'])

    Returns:
        Dictionary mapping file paths to lists of matches
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.eggs']

    results = {}
    directory_path = Path(directory).resolve()

    # Handle different file patterns
    if file_pattern == "*":
        file_patterns = ["**/*"]
    else:
        file_patterns = [f"**/{file_pattern}"]

    for pattern_str in file_patterns:
        for file_path in directory_path.glob(pattern_str):
            if not file_path.is_file():
                continue

            # Check if file is in excluded directory
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue

            # Skip binary files
            if is_binary_file(str(file_path)):
                continue

            matches = search_in_file(str(file_path), pattern, case_sensitive, context_lines)
            if matches:
                relative_path = file_path.relative_to(directory_path)
                results[str(relative_path)] = matches

    return results


def is_binary_file(filepath: str, check_bytes: int = 1024) -> bool:
    """
    Check if a file is binary by reading the first few bytes.

    Args:
        filepath: Path to the file
        check_bytes: Number of bytes to check

    Returns:
        True if the file appears to be binary
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(check_bytes)
            # Check for null bytes, which are common in binary files
            if b'\x00' in chunk:
                return True
            # Check if the file is mostly text characters
            text_characters = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
            non_text = chunk.translate(None, text_characters)
            if len(non_text) / len(chunk) > 0.3:
                return True
    except Exception:
        return True
    return False


def find_definition(directory: str, identifier: str, file_pattern: str = "*.py") -> Dict[str, List[Tuple[int, str]]]:
    """
    Find definitions of a function, class, or variable in the codebase.

    Args:
        directory: Root directory to search
        identifier: Name of the identifier to find
        file_pattern: Glob pattern for files to search

    Returns:
        Dictionary mapping file paths to lists of (line_number, line_content) tuples
    """
    # Common patterns for definitions in different languages
    patterns = {
        "*.py": [
            rf"^def\s+{identifier}\s*\(",
            rf"^class\s+{identifier}\s*[\(:]",
            rf"^async\s+def\s+{identifier}\s*\(",
        ],
        "*.js": [
            rf"function\s+{identifier}\s*\(",
            rf"const\s+{identifier}\s*=",
            rf"let\s+{identifier}\s*=",
            rf"var\s+{identifier}\s*=",
            rf"class\s+{identifier}\s*{{",
        ],
        "*.ts": [
            rf"function\s+{identifier}\s*\(",
            rf"const\s+{identifier}\s*[:=]",
            rf"let\s+{identifier}\s*[:=]",
            rf"class\s+{identifier}\s*{{",
            rf"interface\s+{identifier}\s*{{",
            rf"type\s+{identifier}\s*=",
        ],
        "*.java": [
            rf"class\s+{identifier}\s*{{",
            rf"interface\s+{identifier}\s*{{",
            rf"enum\s+{identifier}\s*{{",
            rf"public\s+.*\s+{identifier}\s*\(",
            rf"private\s+.*\s+{identifier}\s*\(",
        ],
    }

    results = {}
    combined_pattern = "|".join(patterns.get(file_pattern, patterns["*.py"]))

    search_results = search_in_directory(
        directory,
        combined_pattern,
        file_pattern,
        case_sensitive=True,
        context_lines=0
    )

    for filepath, matches in search_results.items():
        results[filepath] = [(line_num, line_text) for line_num, line_text, _ in matches]

    return results


def display_search_results(
    results: Dict[str, List[Tuple[int, str, List[str]]]],
    pattern: str,
    max_results: int = 50
) -> None:
    """
    Display search results in a formatted way.

    Args:
        results: Dictionary of search results from search_in_directory
        pattern: The search pattern that was used
        max_results: Maximum number of results to display
    """
    if not results:
        console.print(f"[yellow]No matches found for pattern:[/yellow] {pattern}")
        return

    total_matches = sum(len(matches) for matches in results.values())
    console.print(Panel(f"[bold cyan]Found {total_matches} matches in {len(results)} files[/bold cyan]", expand=False))

    displayed = 0
    for filepath, matches in sorted(results.items()):
        if displayed >= max_results:
            remaining = total_matches - displayed
            console.print(f"\n[yellow]... and {remaining} more matches (use --max-results to see more)[/yellow]")
            break

        console.print(f"\n[bold magenta]{filepath}[/bold magenta]")

        for line_num, line_text, context in matches:
            if displayed >= max_results:
                break

            console.print(f"  [cyan]Line {line_num}:[/cyan] {line_text}")
            displayed += 1

    console.print()
