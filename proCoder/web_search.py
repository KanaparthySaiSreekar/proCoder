"""Web search capability for proCoder."""

import requests
from typing import List, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json
import urllib.parse

console = Console()


class WebSearcher:
    """Handles web search operations."""

    def __init__(self, enabled: bool = False):
        """
        Initialize the web searcher.

        Args:
            enabled: Whether web search is enabled
        """
        self.enabled = enabled
        self.user_agent = "proCoder/0.5.0 (AI Coding Assistant)"

    def is_enabled(self) -> bool:
        """Check if web search is enabled."""
        return self.enabled

    def enable(self):
        """Enable web search."""
        self.enabled = True
        console.print("[green]Web search enabled[/green]")

    def disable(self):
        """Disable web search."""
        self.enabled = False
        console.print("[yellow]Web search disabled[/yellow]")

    def search(self, query: str, max_results: int = 5) -> Optional[List[Dict[str, str]]]:
        """
        Perform a web search using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, link, and snippet
        """
        if not self.enabled:
            console.print("[yellow]Web search is disabled. Enable it in config or use /websearch enable[/yellow]")
            return None

        console.print(f"[blue]Searching the web for:[/blue] {query}")

        try:
            # Use DuckDuckGo instant answer API (simple, no API key required)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }

            headers = {
                "User-Agent": self.user_agent
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            # Get abstract if available
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", query),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", "")
                })

            # Get related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")
                    })

            # If no results from DDG, try alternative search
            if not results:
                results = self._fallback_search(query, max_results)

            if results:
                self._display_results(results)
                return results
            else:
                console.print("[yellow]No search results found[/yellow]")
                return None

        except requests.RequestException as e:
            console.print(f"[red]Search failed:[/red] {e}")
            return None

    def _fallback_search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """
        Fallback search using HTML parsing of DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of search results
        """
        try:
            # Use DuckDuckGo HTML (lite version)
            url = f"https://lite.duckduckgo.com/lite/"
            data = {"q": query}
            headers = {"User-Agent": self.user_agent}

            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            # Basic HTML parsing (simple extraction)
            results = []
            html = response.text

            # This is a very basic parser - in production, use BeautifulSoup
            # For now, we'll just indicate that search was attempted
            console.print("[dim]Search completed but results require parsing[/dim]")

            return []

        except Exception as e:
            console.print(f"[dim]Fallback search failed: {e}[/dim]")
            return []

    def search_stackoverflow(self, query: str, max_results: int = 5) -> Optional[List[Dict[str, str]]]:
        """
        Search Stack Overflow questions.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of Stack Overflow results
        """
        if not self.enabled:
            console.print("[yellow]Web search is disabled[/yellow]")
            return None

        console.print(f"[blue]Searching Stack Overflow for:[/blue] {query}")

        try:
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                "order": "desc",
                "sort": "relevance",
                "q": query,
                "site": "stackoverflow",
                "pagesize": max_results
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": f"Score: {item.get('score', 0)} | Answers: {item.get('answer_count', 0)} | {item.get('tags', [])}",
                    "score": item.get("score", 0),
                    "answered": item.get("is_answered", False)
                })

            if results:
                self._display_stackoverflow_results(results)
                return results
            else:
                console.print("[yellow]No Stack Overflow results found[/yellow]")
                return None

        except requests.RequestException as e:
            console.print(f"[red]Stack Overflow search failed:[/red] {e}")
            return None

    def search_github(self, query: str, search_type: str = "repositories", max_results: int = 5) -> Optional[List[Dict[str, str]]]:
        """
        Search GitHub repositories or code.

        Args:
            query: Search query
            search_type: Type of search (repositories, code, issues)
            max_results: Maximum results

        Returns:
            List of GitHub results
        """
        if not self.enabled:
            console.print("[yellow]Web search is disabled[/yellow]")
            return None

        console.print(f"[blue]Searching GitHub {search_type} for:[/blue] {query}")

        try:
            url = f"https://api.github.com/search/{search_type}"
            params = {
                "q": query,
                "per_page": max_results,
                "sort": "stars" if search_type == "repositories" else "best match"
            }

            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/vnd.github.v3+json"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("items", []):
                if search_type == "repositories":
                    results.append({
                        "title": item.get("full_name", ""),
                        "link": item.get("html_url", ""),
                        "snippet": item.get("description", "No description"),
                        "stars": item.get("stargazers_count", 0),
                        "language": item.get("language", "Unknown")
                    })
                elif search_type == "code":
                    results.append({
                        "title": item.get("name", ""),
                        "link": item.get("html_url", ""),
                        "snippet": f"Repository: {item.get('repository', {}).get('full_name', 'Unknown')}",
                        "path": item.get("path", "")
                    })

            if results:
                self._display_github_results(results, search_type)
                return results
            else:
                console.print("[yellow]No GitHub results found[/yellow]")
                return None

        except requests.RequestException as e:
            console.print(f"[red]GitHub search failed:[/red] {e}")
            return None

    def _display_results(self, results: List[Dict[str, str]]):
        """Display search results in a formatted table."""
        table = Table(title="Search Results", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="green")
        table.add_column("URL", style="blue", no_wrap=True)

        for i, result in enumerate(results, 1):
            title = result["title"][:60] + "..." if len(result["title"]) > 60 else result["title"]
            link = result["link"][:50] + "..." if len(result["link"]) > 50 else result["link"]
            table.add_row(str(i), title, link)

        console.print(table)

        # Display snippets
        for i, result in enumerate(results, 1):
            if result.get("snippet"):
                console.print(f"\n[bold]{i}. {result['title']}[/bold]")
                console.print(f"[dim]{result['snippet'][:200]}...[/dim]" if len(result['snippet']) > 200 else f"[dim]{result['snippet']}[/dim]")

    def _display_stackoverflow_results(self, results: List[Dict[str, str]]):
        """Display Stack Overflow results."""
        table = Table(title="Stack Overflow Results", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="green")
        table.add_column("Score", justify="right", style="yellow")
        table.add_column("Answered", style="blue")

        for i, result in enumerate(results, 1):
            title = result["title"][:80] + "..." if len(result["title"]) > 80 else result["title"]
            answered = "✓" if result.get("answered") else "✗"
            table.add_row(str(i), title, str(result.get("score", 0)), answered)

        console.print(table)

        console.print("\n[dim]Use the link to view full questions and answers[/dim]")

    def _display_github_results(self, results: List[Dict[str, str]], search_type: str):
        """Display GitHub results."""
        table = Table(title=f"GitHub {search_type.capitalize()} Results", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="green")

        if search_type == "repositories":
            table.add_column("Stars", justify="right", style="yellow")
            table.add_column("Language", style="blue")

            for i, result in enumerate(results, 1):
                table.add_row(
                    str(i),
                    result["title"],
                    str(result.get("stars", 0)),
                    result.get("language", "Unknown")
                )
        else:
            table.add_column("Path", style="blue")

            for i, result in enumerate(results, 1):
                table.add_row(
                    str(i),
                    result["title"],
                    result.get("path", "")
                )

        console.print(table)

    def format_for_ai(self, results: List[Dict[str, str]]) -> str:
        """
        Format search results for AI consumption.

        Args:
            results: Search results

        Returns:
            Formatted string for AI
        """
        if not results:
            return "No search results found."

        formatted = "# Web Search Results\n\n"

        for i, result in enumerate(results, 1):
            formatted += f"## Result {i}: {result['title']}\n"
            formatted += f"**URL:** {result['link']}\n"
            if result.get("snippet"):
                formatted += f"**Summary:** {result['snippet']}\n"
            formatted += "\n"

        return formatted
