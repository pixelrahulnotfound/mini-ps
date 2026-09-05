import pytest

from mcp_server.tools.activities import build_day_itinerary, get_activities_and_attractions
from mcp_server.tools.accommodation import get_accommodation_options
from mcp_server.tools.budget import calculate_trip_budget
from mcp_server.tools.destination import get_destination_overview
from mcp_server.tools.logistics import get_travel_logistics
from mcp_server.tools.timing import get_best_time_to_visit


@pytest.mark.asyncio
async def test_destination_overview_resolves_alias():
    result = await get_destination_overview("Panjim")
    assert result["ok"] is True
    assert result["destination"] == "Goa"
    assert "North Goa" in [zone["name"] for zone in result["zones"]]


@pytest.mark.asyncio
async def test_logistics_exposes_cost_for_budget_chain():
    result = await get_travel_logistics("Goa", "Hyderabad")
    assert result["ok"] is True
    assert result["recommended_cost_per_person"] > 0
    assert result["modes"]["train"]["cost_per_person"] == 1200


@pytest.mark.asyncio
async def test_timing_flags_bad_month():
    result = await get_best_time_to_visit("Ladakh", "January")
    assert result["verdict"] == "inadvisable"
    assert "warning" in result["prominent_warning"].lower()


@pytest.mark.asyncio
async def test_activities_match_food_alias():
    result = await get_activities_and_attractions("Goa", ["seafood"])
    assert result["ok"] is True
    assert result["requested_interests"] == ["food"]
    assert any("food" in item["categories"] for item in result["matched_activities"])


@pytest.mark.asyncio
async def test_itinerary_has_flex_day_for_long_trip():
    result = await build_day_itinerary("Goa", 5, ["beach"], "moderate")
    assert result["ok"] is True
    assert len(result["days"]) == 5
    assert "flex_day" in result["days"][-1]


@pytest.mark.asyncio
async def test_budget_math_and_over_budget_suggestions():
    result = await calculate_trip_budget(
        "Goa", 5, 3, 75000, "mid-range", 5500, 1200
    )
    assert result["breakdown"]["transport"] == 33000
    assert result["total_estimated"] > result["stated_budget"]
    assert result["verdict"] == "Over budget — adjustments needed"
    assert result["suggestions"]


@pytest.mark.asyncio
async def test_accommodation_calculates_rooms():
    result = await get_accommodation_options("Goa", 5, 3, "budget")
    assert result["ok"] is True
    assert result["rooms_needed"] == 2
    assert len(result["recommendations"]) == 3
