from typing import List, Dict, Any
from fastapi import APIRouter
from ..models.schemas import TripCreateRequest

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "scenario-1-solo-weekend",
        "title": "Scenario 1: Solo Traveler - Weekend Getaway",
        "badge": "Solo Travel",
        "tagline": "Quick, stress-free 3-day weekend exploring sights & food with zero decision fatigue.",
        "description": "A solo traveler wants to plan a short weekend trip with limited time to research attractions and routes. Optimized for travel time, walkability, and affordable dining.",
        "preset_data": {
            "destination": "Paris, France",
            "start_date": "2026-06-05",
            "end_date": "2026-06-07",
            "budget_tier": "moderate",
            "budget_amount": 750.0,
            "travel_style": "solo",
            "group_size": 1,
            "interests": ["Food & Dining", "Sightseeing", "Culture"],
            "pace": "balanced",
            "special_notes": "Solo weekend getaway. Prioritize walkable routes, safe evening cafes, and must-see landmarks.",
        },
    },
    {
        "id": "scenario-2-couple-vacation",
        "title": "Scenario 2: Couple - Personalized Romantic Vacation",
        "badge": "Romantic Couple",
        "tagline": "Curated scenic viewpoints, relaxed pacing, premium stays, and sunset dining.",
        "description": "A couple planning a romantic vacation wanting customized experiences rather than generic tourist traps. Features relaxed pacing, curated dining, and interactive day regeneration.",
        "preset_data": {
            "destination": "Amalfi Coast, Italy",
            "start_date": "2026-07-10",
            "end_date": "2026-07-15",
            "budget_tier": "luxury",
            "budget_amount": 3200.0,
            "travel_style": "couple",
            "group_size": 2,
            "interests": ["Food & Dining", "Relaxation", "Sightseeing", "Nature"],
            "pace": "relaxed",
            "special_notes": "Romantic getaway. Scenic coastal drives, intimate cliffside dinners, and leisurely mornings.",
        },
    },
    {
        "id": "scenario-3-group-trip",
        "title": "Scenario 3: Small Group - Multi-Day Adventure",
        "badge": "Small Group",
        "tagline": "Coordinated multi-day adventure balancing diverse interests, shared budget, and smooth group logistics.",
        "description": "A group of friends organizing a multi-day holiday. Automatically structures activities, minimizes group travel delays, and tracks shared budget limits.",
        "preset_data": {
            "destination": "Tokyo, Japan",
            "start_date": "2026-09-01",
            "end_date": "2026-09-06",
            "budget_tier": "moderate",
            "budget_amount": 4500.0,
            "travel_style": "group",
            "group_size": 4,
            "interests": ["Adventure", "Culture", "Food & Dining", "Nightlife"],
            "pace": "fast_paced",
            "special_notes": "Friends group trip. Blend vibrant nightlife, interactive digital art, temple visits, and street food tours.",
        },
    },
]


@router.get("", response_model=List[Dict[str, Any]])
async def list_scenarios():
    """Returns the predefined test scenarios matching prompt requirements."""
    return SCENARIOS


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Retrieve details and prefilled data for a given scenario."""
    for s in SCENARIOS:
        if s["id"] == scenario_id:
            return s
    return SCENARIOS[0]
