"""Destination overview tool."""

from __future__ import annotations

from typing import Any

from mcp_server.utils.data import resolve_destination
from mcp_server.utils.http_client import get_json, live_data_enabled


async def get_destination_overview(destination: str) -> dict[str, Any]:
    key, record = resolve_destination(destination)
    if record:
        result = {
            "ok": True,
            "destination": record["name"],
            "country": record["country"],
            "state": record.get("state"),
            "description": record["description"],
            "known_for": record["known_for"],
            "zones": record["zones"],
            "airport": record["airport"],
            "railhead": record["railhead"],
            "recommended_duration": record["recommended_duration"],
            "source": "destination dataset",
        }
        if live_data_enabled():
            wiki = await get_json(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{record['name'].replace(' ', '_')}",
                headers={"User-Agent": "mini-ps/1.0"},
            )
            if isinstance(wiki, dict) and wiki.get("extract"):
                result["live_summary"] = wiki["extract"]
                result["live_source"] = "Wikipedia REST API"
        return result
    return {
        "ok": False,
        "destination": destination,
        "error": f"No destination profile found for {destination!r}.",
        "known_destination_key": key,
        "source": "destination dataset",
        "suggestion": "Check the destination name or continue with general estimates.",
    }
