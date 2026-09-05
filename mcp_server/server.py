"""FastMCP server exposing travel planning tools."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.activities import (
    build_day_itinerary as build_day_itinerary_impl,
    get_activities_and_attractions as get_activities_and_attractions_impl,
)
from mcp_server.tools.accommodation import get_accommodation_options as get_accommodation_options_impl
from mcp_server.tools.budget import calculate_trip_budget as calculate_trip_budget_impl
from mcp_server.tools.destination import get_destination_overview as get_destination_overview_impl
from mcp_server.tools.logistics import get_travel_logistics as get_travel_logistics_impl
from mcp_server.tools.timing import get_best_time_to_visit as get_best_time_to_visit_impl

mcp = FastMCP(
    "mini-ps travel planner",
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MINIPS_MCP_PORT", os.getenv("MCP_PORT", "3000"))),
)


@mcp.tool()
async def get_destination_overview(destination: str) -> dict:
    """Understand a destination's character, zones, transport gateways, and ideal trip length."""
    return await get_destination_overview_impl(destination)


@mcp.tool()
async def get_travel_logistics(destination: str, origin: str = "Delhi") -> dict:
    """Compare transport modes, rough return costs, travel times, and permit notes."""
    return await get_travel_logistics_impl(destination, origin)


@mcp.tool()
async def get_best_time_to_visit(destination: str, travel_month: str) -> dict:
    """Check seasonal suitability, weather, crowds, festivals, and price impact."""
    return await get_best_time_to_visit_impl(destination, travel_month)


@mcp.tool()
async def get_activities_and_attractions(destination: str, interests: list[str] | None = None) -> dict:
    """Find attractions matched to interests and group them by geographic zone."""
    return await get_activities_and_attractions_impl(destination, interests or [])


@mcp.tool()
async def build_day_itinerary(
    destination: str,
    num_days: int,
    interests: list[str] | None = None,
    pace: str = "moderate",
) -> dict:
    """Build a zone-aware day-by-day itinerary at a relaxed, moderate, or packed pace."""
    return await build_day_itinerary_impl(destination, num_days, interests or [], pace)


@mcp.tool()
async def calculate_trip_budget(
    destination: str,
    num_days: int,
    num_people: int,
    total_budget: float,
    accommodation_preference: str = "mid-range",
    travel_cost_per_person: float = 0,
    activity_cost_per_person_per_day: float = 0,
) -> dict:
    """Calculate return transport, rooms, food, activities, local transport, and a buffer."""
    return await calculate_trip_budget_impl(
        destination,
        num_days,
        num_people,
        total_budget,
        accommodation_preference,
        travel_cost_per_person,
        activity_cost_per_person_per_day,
    )


@mcp.tool()
async def get_accommodation_options(
    destination: str,
    num_nights: int,
    num_people: int,
    preference: str = "mid-range",
) -> dict:
    """Recommend three accommodation options with rates, locations, and booking guidance."""
    return await get_accommodation_options_impl(destination, num_nights, num_people, preference)


def main() -> None:
    transport = os.getenv("MINIPS_MCP_TRANSPORT", "sse")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
