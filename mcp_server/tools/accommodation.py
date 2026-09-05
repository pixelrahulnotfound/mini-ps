"""Accommodation recommendation tool."""

from __future__ import annotations

from typing import Any

from mcp_server.utils.data import load_json, resolve_destination


async def get_accommodation_options(
    destination: str,
    num_nights: int,
    num_people: int,
    preference: str = "mid-range",
) -> dict[str, Any]:
    if num_nights < 1 or num_people < 1:
        return {"ok": False, "error": "num_nights and num_people must be positive.", "source": "local validation"}
    key, record = resolve_destination(destination)
    if not record:
        return {"ok": False, "destination": destination, "error": "No accommodation profile is available.", "source": "accommodation dataset"}
    preference = preference.lower().strip()
    if preference not in {"budget", "mid-range", "luxury"}:
        preference = "mid-range"
    options = load_json("accommodations.json").get(key, {}).get(preference, [])
    if not options:
        return {"ok": False, "destination": record["name"], "error": "No accommodation options are listed for this tier.", "source": "accommodation dataset"}
    rooms = max(1, (num_people + 1) // 2)
    rates = [item["price_per_night"] for item in options]
    return {
        "ok": True,
        "destination": record["name"],
        "preference": preference,
        "num_nights": num_nights,
        "num_people": num_people,
        "rooms_needed": rooms,
        "price_per_night_range": {"min": min(rates), "max": max(rates)},
        "recommendations": options,
        "booking_guidance": "Book early for peak season; use refundable rates when dates are not fixed.",
        "estimated_stay_range": {"min": min(rates) * num_nights * rooms, "max": max(rates) * num_nights * rooms},
        "recommended_booking_platform": "Compare direct property rates with reputable hotel platforms.",
        "source": "accommodation dataset",
    }
