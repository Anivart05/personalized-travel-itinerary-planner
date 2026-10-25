"""
Flask Companion Application for Personalized Travel Itinerary Planner.
Demonstrates Flask framework implementation alongside the primary FastAPI backend.
"""

import sys
from pathlib import Path

# Add backend root to sys.path so it shares models and services
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

import asyncio
from flask import Flask, request, jsonify
from app.models.schemas import TripCreateRequest, DayRegenerateRequest, ActivityCreateUpdateRequest
from app.services.ai_generator import ai_generator
from app.services.database import db_service
from app.services.optimizer import ItineraryOptimizer

flask_app = Flask(__name__)


def run_async(coro):
    """Utility to run async coroutines in synchronous Flask handlers."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@flask_app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "framework": "Flask 3.x",
        "service": "Personalized Travel Itinerary Planner (Flask Service)",
    })


@flask_app.route("/api/trips/generate", methods=["POST"])
def generate_trip():
    data = request.get_json()
    try:
        req = TripCreateRequest(**data)
        itinerary = run_async(ai_generator.generate_itinerary(req))
        saved = db_service.save_trip(itinerary)
        return jsonify(saved.model_dump()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@flask_app.route("/api/trips", methods=["GET"])
def list_trips():
    limit = int(request.args.get("limit", 50))
    trips = db_service.list_trips(limit=limit)
    return jsonify([t.model_dump() for t in trips])


@flask_app.route("/api/trips/<trip_id>", methods=["GET"])
def get_trip(trip_id):
    trip = db_service.get_trip(trip_id)
    if not trip:
        return jsonify({"error": "Trip not found"}), 404
    return jsonify(trip.model_dump())


@flask_app.route("/api/trips/<trip_id>/regenerate-day", methods=["POST"])
def regenerate_day(trip_id):
    trip = db_service.get_trip(trip_id)
    if not trip:
        return jsonify({"error": "Trip not found"}), 404

    data = request.get_json()
    req = DayRegenerateRequest(**data)
    try:
        updated = run_async(ai_generator.regenerate_day(trip, req))
        saved = db_service.save_trip(updated)
        return jsonify(saved.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Starting Flask Service on http://localhost:5000")
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
