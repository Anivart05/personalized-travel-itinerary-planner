import asyncio
import pytest
from app.models.schemas import TripCreateRequest, DayRegenerateRequest
from app.services.ai_generator import ai_generator


@pytest.mark.asyncio
async def test_generate_itinerary_scenario_1_solo():
    req = TripCreateRequest(
        destination="Paris, France",
        start_date="2026-06-05",
        end_date="2026-06-07",
        budget_tier="moderate",
        budget_amount=750.0,
        travel_style="solo",
        group_size=1,
        interests=["Food & Dining", "Sightseeing"],
        pace="balanced",
    )
    itinerary = await ai_generator.generate_itinerary(req)
    assert itinerary is not None
    assert itinerary.duration_days == 3
    assert len(itinerary.days) == 3
    assert itinerary.travel_style == "solo"
    assert len(itinerary.days[0].activities) >= 3


@pytest.mark.asyncio
async def test_regenerate_single_day_scenario_2():
    req = TripCreateRequest(
        destination="Amalfi Coast, Italy",
        start_date="2026-07-10",
        end_date="2026-07-12",
        budget_tier="luxury",
        budget_amount=2000.0,
        travel_style="couple",
        group_size=2,
        interests=["Relaxation", "Food & Dining"],
        pace="relaxed",
    )
    itinerary = await ai_generator.generate_itinerary(req)
    orig_day_2_theme = itinerary.days[1].theme

    regen_req = DayRegenerateRequest(
        day_number=2,
        refinement_prompt="Focus on romantic sunset wine tasting and private boat tour",
    )
    updated_trip = await ai_generator.regenerate_day(itinerary, regen_req)
    assert updated_trip is not None
    assert updated_trip.days[1].day_number == 2
    assert len(updated_trip.days[1].activities) > 0


@pytest.mark.asyncio
async def test_copilot_assistant():
    resp = await ai_generator.ask_copilot(
        question="What should I pack for Paris in the summer?",
        destination="Paris, France",
    )
    assert resp is not None
    assert len(resp.answer) > 20
    assert len(resp.suggested_actions) > 0
