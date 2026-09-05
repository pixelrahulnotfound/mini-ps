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
    destination = Prompt.ask("Destination", default="Goa")
    origin = Prompt.ask("Starting from", default="Hyderabad")
    month = Prompt.ask("Travel month", default="December")
    days = Prompt.ask("Number of days", default="5")
    people = Prompt.ask("People", default="3")
    budget = Prompt.ask("Total budget (INR)", default="75000")
    interests = Prompt.ask("Interests", default="beaches, seafood, nightlife")
    pace = Prompt.ask("Pace", choices=["relaxed", "moderate", "packed"], default="moderate")
    stay = Prompt.ask("Stay style", choices=["budget", "mid-range", "luxury"], default="mid-range")
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
            answer = await agent.run(query)
    except Exception as exc:
        console.print(
            Panel(
                f"[bold red]Could not connect to MCP server.[/bold red]\n\n"
                f"{exc}\n\nStart it with: [bold]python -m mcp_server.server[/bold]",
                title="Connection Error",
                border_style="red",
            )
        )
        raise
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
