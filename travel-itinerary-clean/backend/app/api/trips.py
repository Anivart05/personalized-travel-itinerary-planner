import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from ..models.schemas import (
    TripCreateRequest,
    TripItinerary,
    DayPlan,
    Activity,
    DayRegenerateRequest,
    ActivityCreateUpdateRequest,
    ChatQueryRequest,
    ChatQueryResponse,
)
from ..services.database import db_service
from ..services.ai_generator import ai_generator
from ..services.optimizer import ItineraryOptimizer
from .auth import get_current_user_id

router = APIRouter(prefix="/trips", tags=["Trips & Itineraries"])


@router.post("/generate", response_model=TripItinerary)
async def generate_trip(
    req: TripCreateRequest,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Generate a personalized AI travel itinerary based on preferences,
    budget, travel style, and duration.
    """
    try:
        itinerary = await ai_generator.generate_itinerary(req)
        itinerary.user_id = user_id
        saved = db_service.save_trip(itinerary, user_id=user_id)
        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate trip: {str(e)}")


@router.get("", response_model=List[TripItinerary])
async def list_trips(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Retrieve saved itineraries."""
    return db_service.list_trips(user_id=user_id, limit=limit, offset=offset)


@router.get("/{trip_id}", response_model=TripItinerary)
async def get_trip(trip_id: str):
    """Get full details of a specific itinerary."""
    trip = db_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.put("/{trip_id}", response_model=TripItinerary)
async def update_trip(trip_id: str, trip_data: TripItinerary):
    """Update an existing itinerary."""
    existing = db_service.get_trip(trip_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip_data.id = trip_id
    trip_data.updated_at = datetime.utcnow().isoformat()
    optimized = ItineraryOptimizer.optimize_itinerary(trip_data)
    saved = db_service.save_trip(optimized)
    return saved


@router.delete("/{trip_id}")
async def delete_trip(trip_id: str):
    """Delete a saved itinerary."""
    success = db_service.delete_trip(trip_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trip not found or already deleted")
    return {"message": "Trip successfully deleted", "trip_id": trip_id}


@router.post("/{trip_id}/regenerate-day", response_model=TripItinerary)
async def regenerate_trip_day(trip_id: str, req: DayRegenerateRequest):
    """
    Regenerate a specific day of the trip using AI with user refinements.
    Addresses Scenario 2 requirement: 'modify activities, regenerate specific days'.
    """
    trip = db_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    try:
        updated_trip = await ai_generator.regenerate_day(trip, req)
        saved = db_service.save_trip(updated_trip)
        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration error: {str(e)}")


@router.post("/{trip_id}/days/{day_number}/activities", response_model=TripItinerary)
async def add_activity(
    trip_id: str,
    day_number: int,
    activity_data: ActivityCreateUpdateRequest,
):
    """Add a new custom activity to a specific day."""
    trip = db_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    target_day = None
    for day in trip.days:
        if day.day_number == day_number:
            target_day = day
            break

    if not target_day:
        raise HTTPException(status_code=404, detail=f"Day {day_number} not found")

    new_activity = Activity(
        id=f"act_{uuid.uuid4().hex[:8]}",
        title=activity_data.title,
        category=activity_data.category,
        time_slot=activity_data.time_slot,
        start_time=activity_data.start_time,
        end_time=activity_data.end_time,
        description=activity_data.description,
        location=activity_data.location,
        lat=activity_data.lat,
        lng=activity_data.lng,
        cost_estimate=activity_data.cost_estimate,
        transit_info=activity_data.transit_info,
        booking_tips=activity_data.booking_tips,
        is_completed=False,
    )
    target_day.activities.append(new_activity)

    trip.updated_at = datetime.utcnow().isoformat()
    optimized = ItineraryOptimizer.optimize_itinerary(trip)
    saved = db_service.save_trip(optimized)
    return saved


@router.put("/{trip_id}/activities/{activity_id}", response_model=TripItinerary)
async def edit_activity(
    trip_id: str,
    activity_id: str,
    activity_data: ActivityCreateUpdateRequest,
):
    """Edit an existing activity."""
    trip = db_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    found = False
    for day in trip.days:
        for idx, act in enumerate(day.activities):
            if act.id == activity_id:
                day.activities[idx] = Activity(
                    id=activity_id,
                    title=activity_data.title,
                    category=activity_data.category,
                    time_slot=activity_data.time_slot,
                    start_time=activity_data.start_time,
                    end_time=activity_data.end_time,
                    description=activity_data.description,
                    location=activity_data.location,
                    lat=activity_data.lat if activity_data.lat is not None else act.lat,
                    lng=activity_data.lng if activity_data.lng is not None else act.lng,
                    cost_estimate=activity_data.cost_estimate,
                    transit_info=activity_data.transit_info or act.transit_info,
                    booking_tips=activity_data.booking_tips or act.booking_tips,
                    is_completed=act.is_completed,
                )
                found = True
                break
        if found:
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")

    trip.updated_at = datetime.utcnow().isoformat()
    optimized = ItineraryOptimizer.optimize_itinerary(trip)
    saved = db_service.save_trip(optimized)
    return saved


@router.delete("/{trip_id}/activities/{activity_id}", response_model=TripItinerary)
async def delete_activity(trip_id: str, activity_id: str):
    """Delete an activity from a day and recalculate budget."""
    trip = db_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    found = False
    for day in trip.days:
        orig_len = len(day.activities)
        day.activities = [a for a in day.activities if a.id != activity_id]
        if len(day.activities) < orig_len:
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Activity not found")

    trip.updated_at = datetime.utcnow().isoformat()
    optimized = ItineraryOptimizer.optimize_itinerary(trip)
    saved = db_service.save_trip(optimized)
    return saved


@router.get("/share/{share_token}", response_model=TripItinerary)
async def get_shared_trip(share_token: str):
    """
    Public read-only link for shared group trips (Scenario 3 coordination).
    """
    trip = db_service.get_trip_by_share_token(share_token)
    if not trip:
        raise HTTPException(status_code=404, detail="Shared trip link not found or expired")
    return trip


@router.post("/copilot", response_model=ChatQueryResponse)
async def copilot_chat(req: ChatQueryRequest):
    """
    AI Travel Copilot assistant for destination questions, packing, tips, and logistics.
    """
    resp = await ai_generator.ask_copilot(req.question, req.destination)
    return resp
