"""Activity matching and itinerary generation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from mcp_server.utils.data import resolve_destination

VALID_INTERESTS = {
    "beach", "history", "adventure", "food", "nightlife", "wildlife",
    "temples", "shopping", "trekking", "art", "family", "mountains",
}
PACE_LIMITS = {"relaxed": 2, "moderate": 3, "packed": 4}


def _normalise_interests(interests: list[str]) -> list[str]:
    values = []
    for item in interests:
        value = item.strip().lower()
        if value == "seafood":
            value = "food"
        if value not in values:
            values.append(value)
    return values


async def get_activities_and_attractions(
    destination: str,
    interests: list[str] | None = None,
) -> dict[str, Any]:
    _, record = resolve_destination(destination)
    if not record:
        return {
            "ok": False,
            "destination": destination,
            "error": "No activity profile is available for this destination.",
            "source": "activity dataset",
        }
    requested = _normalise_interests(interests or [])
    unknown = sorted(set(requested) - VALID_INTERESTS)
    activities = record.get("activities", [])
    matched = [
        item for item in activities
        if not requested or set(item.get("categories", [])) & set(requested)
    ]
    if not matched:
        matched = activities[:]
    must_do = activities[: min(3, len(activities))]
    groups: dict[str, list[str]] = defaultdict(list)
    for item in matched:
        groups[item["zone"]].append(item["name"])
    per_person_day = _estimate_daily_cost(matched, requested)
    return {
        "ok": True,
        "destination": record["name"],
        "requested_interests": requested,
        "unknown_interests": unknown,
        "matched_activities": matched,
        "must_do": must_do,
        "suggested_zone_groupings": dict(groups),
        "activity_cost_estimate_per_person_per_day": per_person_day,
        "source": "activity dataset",
    }


def _estimate_daily_cost(activities: list[dict[str, Any]], interests: list[str]) -> int:
    if not activities:
        return 0
    total = sum(int(item.get("cost_per_person", 0)) for item in activities[:4])
    days = max(1, min(4, len(activities)))
    estimate = round(total / days / 50) * 50
    if "food" in interests:
        estimate += 250
    return max(250, estimate)


async def build_day_itinerary(
    destination: str,
    num_days: int,
    interests: list[str] | None = None,
    pace: str = "moderate",
) -> dict[str, Any]:
    _, record = resolve_destination(destination)
    if not record:
        return {
            "ok": False,
            "destination": destination,
            "error": "No activity profile is available for this destination.",
            "source": "itinerary engine",
        }
    if num_days < 1 or num_days > 30:
        return {"ok": False, "error": "num_days must be between 1 and 30.", "source": "local validation"}
    pace = pace.lower().strip()
    if pace not in PACE_LIMITS:
        pace = "moderate"
    requested = _normalise_interests(interests or [])
    activities = record["activities"]
    matched = [item for item in activities if not requested or set(item["categories"]) & set(requested)]
    if not matched:
        matched = activities[:]
    zone_order: list[str] = []
    for item in matched:
        if item["zone"] not in zone_order:
            zone_order.append(item["zone"])
    days = []
    for day_number in range(1, num_days + 1):
        zone = zone_order[(day_number - 1) % len(zone_order)]
        pool = [item for item in matched if item["zone"] == zone] or matched
        offset = ((day_number - 1) // max(1, len(zone_order))) * PACE_LIMITS[pace]
        selected = [pool[(offset + index) % len(pool)] for index in range(min(PACE_LIMITS[pace], len(pool)))]
        slots = ["morning", "afternoon", "evening"]
        plan = {}
        for index, item in enumerate(selected[:3]):
            plan[slots[index]] = {
                "activity": item["name"],
                "description": item["description"],
                "estimated_cost_per_person": item.get("cost_per_person", 0),
            }
        days.append({
            "day": day_number,
            "theme": f"{zone}: {selected[0]['name']}",
            "zone": zone,
            "activities": plan,
            "meal_stop": _meal_stop(record["name"], requested, day_number),
            "travel_note": "Keep activities in the same zone to reduce transfers." if len(selected) > 1 else "Leave room for a slow local wander.",
        })
    if num_days >= 5:
        days[-1]["flex_day"] = "Keep this day flexible for weather, rest, shopping, or a favourite place revisited."
    return {
        "ok": True,
        "destination": record["name"],
        "pace": pace,
        "days": days,
        "source": "itinerary engine",
    }


def _meal_stop(destination: str, interests: list[str], day_number: int) -> dict[str, Any]:
    if destination == "Goa":
        return {"type": "local seafood or thali", "estimated_cost_per_person": 700 if "food" in interests else 450}
    if destination == "Jaipur":
        return {"type": "Rajasthani thali and market snack", "estimated_cost_per_person": 600}
    if destination == "Manali":
        return {"type": "mountain cafe meal", "estimated_cost_per_person": 500}
    if destination == "Ladakh":
        return {"type": "simple local meal and tea", "estimated_cost_per_person": 650}
    return {"type": "local meal", "estimated_cost_per_person": 500}
