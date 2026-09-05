"""Budget arithmetic and adjustment suggestions."""

from __future__ import annotations

import math
from typing import Any

from mcp_server.utils.data import resolve_destination


async def calculate_trip_budget(
    destination: str,
    num_days: int,
    num_people: int,
    total_budget: float,
    accommodation_preference: str = "mid-range",
    travel_cost_per_person: float = 0,
    activity_cost_per_person_per_day: float = 0,
) -> dict[str, Any]:
    if num_days < 1 or num_people < 1 or total_budget < 0:
        return {"ok": False, "error": "num_days and num_people must be positive, and total_budget cannot be negative.", "source": "local validation"}
    preference = accommodation_preference.lower().strip()
    if preference not in {"budget", "mid-range", "luxury"}:
        preference = "mid-range"
    _, record = resolve_destination(destination)
    if not record:
        return {"ok": False, "destination": destination, "error": "No cost profile is available for this destination.", "source": "cost dataset"}

    nights = max(1, num_days)
    rooms = max(1, math.ceil(num_people / 2))
    food_rate = record["food_per_person_per_day"][preference]
    accommodation_rate = record["accommodation_per_night"][preference]
    transport = round(float(travel_cost_per_person) * num_people * 2)
    accommodation = round(accommodation_rate * nights * rooms)
    food = round(food_rate * num_people * num_days)
    activities = round(float(activity_cost_per_person_per_day) * num_people * num_days)
    local_transport = round(record["local_transport_daily"] * num_days)
    subtotal = transport + accommodation + food + activities + local_transport
    miscellaneous = round(subtotal * 0.10)
    total_estimated = subtotal + miscellaneous
    difference = round(float(total_budget) - total_estimated)
    if difference >= total_estimated * 0.15:
        verdict = "Comfortable"
    elif difference >= 0:
        verdict = "Tight but doable"
    else:
        verdict = "Over budget — adjustments needed"
    result: dict[str, Any] = {
        "ok": True,
        "destination": record["name"],
        "currency": "INR",
        "num_days": num_days,
        "num_nights": nights,
        "num_people": num_people,
        "accommodation_preference": preference,
        "assumptions": {
            "rooms_needed": rooms,
            "return_transport": "travel_cost_per_person × people × 2",
            "buffer_rate": "10% of pre-buffer subtotal",
        },
        "breakdown": {
            "transport": transport,
            "accommodation": accommodation,
            "food": food,
            "activities": activities,
            "local_transport": local_transport,
            "miscellaneous_buffer": miscellaneous,
        },
        "total_estimated": total_estimated,
        "stated_budget": round(float(total_budget)),
        "surplus": max(0, difference),
        "deficit": max(0, -difference),
        "verdict": verdict,
        "source": "cost dataset and inputs",
    }
    if difference < 0:
        result["suggestions"] = _cut_suggestions(record, preference, num_people, nights, difference)
    else:
        result["upgrade_suggestions"] = _upgrade_suggestions(record, preference, difference)
    return result


def _cut_suggestions(record: dict[str, Any], preference: str, people: int, nights: int, difference: int) -> list[str]:
    suggestions = [
        "Compare train or bus travel with the current transport estimate before booking flights.",
        "Reduce one paid activity day or substitute a free walk, beach, market, or viewpoint.",
    ]
    if preference != "budget":
        saving = record["accommodation_per_night"][preference] - record["accommodation_per_night"]["budget"]
        suggestions.insert(1, f"Switch to budget accommodation; saves about ₹{saving * nights * max(1, math.ceil(people / 2)):,}.")
    suggestions.append(f"The current estimate is ₹{abs(difference):,} above the stated budget; keep a 10% buffer if possible.")
    return suggestions


def _upgrade_suggestions(record: dict[str, Any], preference: str, surplus: int) -> list[str]:
    suggestions = ["Keep the buffer for price changes and weather-related transport changes."]
    if preference != "luxury":
        suggestions.append("Use part of the surplus for one nicer stay or a better-located room.")
    suggestions.append(f"Available headroom is approximately ₹{surplus:,}; add experiences only after transport is booked.")
    return suggestions
