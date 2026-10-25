import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Personalized Travel Itinerary Planner" in data["app"]


def test_list_scenarios():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    ids = [s["id"] for s in data]
    assert "scenario-1-solo-weekend" in ids
    assert "scenario-2-couple-vacation" in ids
    assert "scenario-3-group-trip" in ids


def test_generate_and_get_trip():
    payload = {
        "destination": "Rome, Italy",
        "start_date": "2026-08-01",
        "end_date": "2026-08-03",
        "budget_tier": "moderate",
        "budget_amount": 900.0,
        "travel_style": "couple",
        "group_size": 2,
        "interests": ["Culture", "Food & Dining"],
        "pace": "balanced",
    }
    create_res = client.post("/api/trips/generate", json=payload)
    assert create_res.status_code == 200
    trip = create_res.json()
    assert trip["destination"] == "Rome, Italy"
    assert trip["duration_days"] == 3
    assert len(trip["days"]) == 3

    # Retrieve trip
    trip_id = trip["id"]
    get_res = client.get(f"/api/trips/{trip_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == trip_id


def test_copilot_api():
    payload = {
        "destination": "Tokyo, Japan",
        "question": "Do I need cash or is credit card okay?",
    }
    res = client.post("/api/trips/copilot", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
