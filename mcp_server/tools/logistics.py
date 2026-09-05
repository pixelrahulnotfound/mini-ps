"""Transport and logistics tool."""

from __future__ import annotations

from typing import Any

from mcp_server.utils.data import load_json, resolve_destination
from mcp_server.utils.http_client import get_json, live_data_enabled


def _route_key(origin: str, destination: str) -> str:
    return f"{origin.strip().lower()}->{destination.strip().lower()}"


async def get_travel_logistics(destination: str, origin: str = "Delhi") -> dict[str, Any]:
    _, record = resolve_destination(destination)
    canonical_destination = record["name"] if record else destination
    routes = load_json("transport.json")
    route = routes.get(_route_key(origin, canonical_destination))
    if route is None:
        route = routes.get(_route_key(origin, destination))
    if route is None:
        route = dict(routes["default"])
        route["origin"] = origin
        route["destination"] = canonical_destination
        route["note"] = "No exact city pair found; using estimated costs."

    modes = {
        name: data for name, data in route.items()
        if name in {"flight", "train", "bus", "road"} and isinstance(data, dict)
    }
    cheapest = min(modes, key=lambda name: modes[name].get("cost_per_person", float("inf")))
    fastest = min(modes, key=lambda name: _duration_minutes(modes[name].get("duration", "")))
    recommendation = "train" if cheapest == "train" and modes[cheapest]["cost_per_person"] <= modes.get("flight", {}).get("cost_per_person", 10**9) * 0.35 else fastest
    permits = []
    if canonical_destination.lower() == "ladakh":
        permits.append("Carry valid photo ID and check current protected-area permit requirements for Nubra and Pangong.")

    result = {
        "ok": True,
        "origin": origin,
        "destination": canonical_destination,
        "modes": modes,
        "road_distance_km": route.get("road_distance_km"),
        "cheapest_mode": cheapest,
        "fastest_mode": fastest,
        "recommended_mode": recommendation,
        "recommended_cost_per_person": modes[recommendation]["cost_per_person"],
        "visa_or_permit_notes": permits or ["No special permits noted; verify entry requirements before travel."],
        "source": "transport dataset",
    }
    if live_data_enabled():
        geocode = await get_json(
            "https://nominatim.openstreetmap.org/search",
            params={"q": canonical_destination, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": "mini-ps/1.0"},
        )
        if isinstance(geocode, list) and geocode:
            result["geocoded_destination"] = {
                "display_name": geocode[0].get("display_name"),
                "latitude": geocode[0].get("lat"),
                "longitude": geocode[0].get("lon"),
            }
            result["live_source"] = "Nominatim"
    return result


def _duration_minutes(value: str) -> int:
    """Best-effort duration sorting; unknown values go to the end."""
    if not value or value == "varies":
        return 999_999
    import re

    hours = re.search(r"(\d+)\s*h", value)
    minutes = re.search(r"(\d+)\s*m", value)
    return (int(hours.group(1)) if hours else 0) * 60 + (int(minutes.group(1)) if minutes else 0)
