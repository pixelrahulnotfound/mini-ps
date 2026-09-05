"""CLI for mini-ps travel planner."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from agent.agent import MiniPSAgent
from agent.config import get_settings
from agent.mcp_client import MCPClient

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="mini-ps — travel planner CLI")
    parser.add_argument("--query", help="Run planning request directly.")
    parser.add_argument("--mcp-url", help="Override MCP SSE URL.")
    return parser


def intake_query() -> str:
    console.print()
    console.print(
        Panel.fit(
            "[bold]mini-ps[/bold]\nTravel Planner CLI",
            border_style="blue",
            padding=(1, 4),
        )
    )
    console.print("[bold]Enter trip details:[/bold]\n")
    destination = Prompt.ask("Destination (eg. Goa)", default="Goa", show_default=False)
    origin = Prompt.ask("Starting from (eg. Hyderabad)", default="Hyderabad", show_default=False)
    month = Prompt.ask("Travel month (eg. December)", default="December", show_default=False)
    days = Prompt.ask("Number of days (eg. 5)", default="5", show_default=False)
    people = Prompt.ask("Number of people (eg. 3)", default="3", show_default=False)
    budget = Prompt.ask("Total budget in INR (eg. 75000)", default="75000", show_default=False)
    interests = Prompt.ask("Interests (eg. beaches, seafood, nightlife)", default="beaches, seafood, nightlife", show_default=False)
    pace = Prompt.ask("Pace [relaxed/moderate/packed] (eg. moderate)", choices=["relaxed", "moderate", "packed"], default="moderate", show_choices=False, show_default=False)
    stay = Prompt.ask("Stay style [budget/mid-range/luxury] (eg. mid-range)", choices=["budget", "mid-range", "luxury"], default="mid-range", show_choices=False, show_default=False)
    return (
        f"Plan a {days}-day trip to {destination} for {people} people, travelling from {origin} "
        f"in {month}. The total budget is ₹{budget}. Interests: {interests}. "
        f"Use a {pace} pace and {stay} accommodation. Give me a complete practical plan."
    )


async def trace_event(event: dict[str, Any]) -> None:
    kind = event.get("type")
    if kind == "tools_discovered":
        console.print(f"[cyan]• {event['count']} MCP tools discovered[/cyan]")
    elif kind == "model_step":
        console.print(f"[dim]• Thinking (step {event['step']})…[/dim]")
    elif kind == "tool_start":
        console.print(
            f"[yellow]• Calling tool:[/yellow] [bold]{event['name']}[/bold] "
            f"[dim]({_short_args(event.get('arguments', {}))})[/dim]"
        )
    elif kind == "tool_end":
        console.print(f"[green]✓[/green] Tool [bold]{event['name']}[/bold] completed")
    elif kind == "limit":
        console.print("[red]⚠[/red] Step limit reached.")


def _short_args(arguments: dict[str, Any]) -> str:
    rendered = ", ".join(f"{key}={value}" for key, value in arguments.items())
    return rendered[:110]


def print_header(query: str) -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row(Text("Trip Query", style="bold"), Text(query))
    console.print(Panel(table, border_style="blue", padding=(0, 1)))
    console.print()


async def run(query: str, mcp_url: str | None = None) -> None:
    settings = get_settings()
    url = mcp_url or settings.mcp_url
    print_header(query)
    try:
        async with MCPClient(url) as mcp_client:
            agent = MiniPSAgent(mcp_client, settings=settings, trace=trace_event)
            try:
                answer = await agent.run(query)
            except Exception as exc:
                console.print(
                    Panel(
                        f"[bold red]LLM Request Failed:[/bold red]\n\n"
                        f"{exc}\n\n"
                        f"Check that your LLM endpoint is running at [bold]{settings.llm_base_url}[/bold]",
                        title="LLM Connection Error",
                        border_style="red",
                    )
                )
                return
    except Exception as exc:
        console.print(
            Panel(
                f"[bold red]Could not connect to MCP server.[/bold red]\n\n"
                f"{exc}\n\nStart it with: [bold]python -m mcp_server.server[/bold]",
                title="MCP Connection Error",
                border_style="red",
            )
        )
        return
    console.print()
    console.print(
        Panel(
            Markdown(answer),
            title="[bold]Trip Plan[/bold]",
            border_style="green",
            padding=(1, 2),
        )
    )


def main() -> None:
    args = build_parser().parse_args()
    query = args.query or intake_query()
    asyncio.run(run(query, args.mcp_url))


if __name__ == "__main__":
    main()
