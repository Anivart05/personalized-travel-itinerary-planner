from app.models.schemas import TripCreateRequest, Activity, DayPlan, BudgetBreakdown


def test_trip_create_request_valid():
    req = TripCreateRequest(
        destination="Paris, France",
        start_date="2026-06-01",
        end_date="2026-06-04",
        budget_tier="moderate",
        budget_amount=1200.0,
        travel_style="solo",
        group_size=1,
        interests=["Sightseeing", "Food & Dining"],
        pace="balanced",
    )
    assert req.destination == "Paris, France"
    assert req.group_size == 1
    assert "Sightseeing" in req.interests


def test_activity_model():
    act = Activity(
        id="act_001",
        title="Louvre Museum",
        category="attraction",
        time_slot="morning",
        start_time="09:00 AM",
        end_time="11:30 AM",
        description="Art gallery and Mona Lisa",
        location="Paris Central",
        lat=48.8606,
        lng=2.3376,
        cost_estimate=22.0,
    )
    assert act.id == "act_001"
    assert act.cost_estimate == 22.0
    assert act.category == "attraction"


def test_budget_breakdown_status():
    b = BudgetBreakdown(
        total_estimated_cost=950.0,
        user_budget=1000.0,
        status="within_budget",
    )
    assert b.status == "within_budget"
    assert b.total_estimated_cost <= b.user_budget
