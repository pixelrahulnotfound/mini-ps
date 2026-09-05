"""Season and weather tool."""

from __future__ import annotations

from typing import Any

from mcp_server.utils.data import month_name, resolve_destination


async def get_best_time_to_visit(destination: str, travel_month: str) -> dict[str, Any]:
    _, record = resolve_destination(destination)
    month = month_name(travel_month)
    if not record:
        return {
            "ok": False,
            "destination": destination,
            "travel_month": month,
            "error": "No seasonal profile is available for this destination.",
            "source": "seasonal dataset",
        }
    season = record.get("seasons", {}).get(month)
    if not season:
        return {
            "ok": False,
            "destination": record["name"],
            "travel_month": month,
            "error": f"No seasonal profile is available for {month}.",
            "source": "seasonal dataset",
        }
    result: dict[str, Any] = {
        "ok": True,
        "destination": record["name"],
        "travel_month": month,
        **season,
        "festivals_or_events": record.get("festivals", {}).get(month, []),
        "source": "seasonal dataset",
    }
    if season["verdict"] == "inadvisable":
        result["prominent_warning"] = "Warning: The requested month is off-season for this destination. Keep outdoor and travel plans flexible."
    elif season["season"] == "peak":
        result["prominent_warning"] = "Peak season: Expect higher accommodation rates and larger crowds."
    return result
