from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ==========================================
# AUTH SCHEMAS
# ==========================================

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str = "Traveler"


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==========================================
# ITINERARY & ACTIVITY SCHEMAS
# ==========================================

class Activity(BaseModel):
    id: str = Field(..., description="Unique ID for activity")
    title: str = Field(..., description="Title of the activity or venue")
    category: str = Field(
        ...,
        description="attraction | dining | accommodation | transit | leisure",
    )
    time_slot: str = Field(
        ...,
        description="morning | afternoon | evening | night",
    )
    start_time: str = Field("09:00 AM", description="Display start time")
    end_time: str = Field("11:30 AM", description="Display end time")
    description: str = Field(..., description="Detailed description and experience")
    location: str = Field(..., description="Location name or address")
    lat: Optional[float] = Field(None, description="Latitude for mapping")
    lng: Optional[float] = Field(None, description="Longitude for mapping")
    cost_estimate: float = Field(0.0, description="Estimated cost in USD")
    transit_info: Optional[str] = Field(
        None, description="Transit/commute instructions from previous stop"
    )
    booking_tips: Optional[str] = Field(
        None, description="Reservation or ticket booking advice"
    )
    is_completed: bool = Field(False, description="Whether traveler has completed this")


class DayPlan(BaseModel):
    day_number: int = Field(..., description="Day index (1-based)")
    date: str = Field(..., description="Date formatted YYYY-MM-DD")
    theme: str = Field(..., description="Theme for the day")
    summary: str = Field(..., description="Daily executive summary")
    estimated_daily_cost: float = Field(0.0, description="Sum of activity costs")
    activities: List[Activity] = Field(default_factory=list)


class BudgetBreakdown(BaseModel):
    currency: str = "USD"
    total_estimated_cost: float = 0.0
    accommodations: float = 0.0
    dining: float = 0.0
    attractions: float = 0.0
    transit: float = 0.0
    miscellaneous: float = 0.0
    user_budget: Optional[float] = None
    status: str = "within_budget"  # within_budget, under_budget, over_budget


class TripCreateRequest(BaseModel):
    destination: str = Field(..., min_length=2, example="Paris, France")
    start_date: str = Field(..., example="2026-06-01")
    end_date: str = Field(..., example="2026-06-04")
    budget_tier: str = Field(
        "moderate",
        description="backpacker | budget | moderate | luxury | ultra_luxury",
    )
    budget_amount: Optional[float] = Field(
        None, description="User target budget amount in USD"
    )
    travel_style: str = Field(
        "solo",
        description="solo | couple | group | family | business",
    )
    group_size: int = Field(1, ge=1, le=50)
    interests: List[str] = Field(
        default_factory=lambda: ["Sightseeing", "Food & Dining", "Culture"]
    )
    pace: str = Field(
        "balanced",
        description="relaxed | balanced | fast_paced",
    )
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    special_notes: Optional[str] = Field(
        None, description="Extra instructions like anniversary, mobility needs, etc."
    )


class DayRegenerateRequest(BaseModel):
    day_number: int = Field(..., ge=1)
    refinement_prompt: Optional[str] = Field(
        None, description="What to change or focus on (e.g. 'more outdoors, less museums')"
    )
    pace_override: Optional[str] = None
    interests_override: Optional[List[str]] = None


class ActivityCreateUpdateRequest(BaseModel):
    title: str
    category: str = "attraction"
    time_slot: str = "morning"
    start_time: str = "09:00 AM"
    end_time: str = "11:00 AM"
    description: str = ""
    location: str = ""
    cost_estimate: float = 0.0
    transit_info: Optional[str] = None
    booking_tips: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class TripItinerary(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    destination: str
    country: Optional[str] = None
    start_date: str
    end_date: str
    duration_days: int
    travel_style: str
    group_size: int
    budget_tier: str
    budget_breakdown: BudgetBreakdown
    overview: str
    packing_essentials: List[str] = Field(default_factory=list)
    local_insights: List[str] = Field(default_factory=list)
    days: List[DayPlan] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    share_token: Optional[str] = None


class ChatQueryRequest(BaseModel):
    trip_id: Optional[str] = None
    destination: Optional[str] = None
    question: str
    context: Optional[dict] = None


class ChatQueryResponse(BaseModel):
    answer: str
    suggested_actions: List[str] = Field(default_factory=list)
