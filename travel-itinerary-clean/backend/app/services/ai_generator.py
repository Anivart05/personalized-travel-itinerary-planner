import json
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import httpx

from ..config import settings
from ..models.schemas import (
    TripCreateRequest,
    TripItinerary,
    DayPlan,
    Activity,
    BudgetBreakdown,
    DayRegenerateRequest,
    ChatQueryResponse,
)
from .optimizer import ItineraryOptimizer

# Coordinate & attraction presets for key popular cities to enrich plans
CITY_KNOWLEDGE_BASE = {
    "paris": {
        "lat": 48.8566,
        "lng": 2.3522,
        "country": "France",
        "highlights": [
            ("Louvre Museum", 48.8606, 2.3376, "attraction", 22.0),
            ("Eiffel Tower & Champ de Mars", 48.8584, 2.2945, "attraction", 30.0),
            ("Montmartre & Sacré-Cœur", 48.8867, 2.3431, "attraction", 0.0),
            ("Café de Flore in Saint-Germain", 48.8542, 2.3328, "dining", 28.0),
            ("Musée d'Orsay Impressionists", 48.8600, 2.3266, "attraction", 18.0),
            ("Le Marais Historic District & Bakeries", 48.8575, 2.3622, "dining", 20.0),
            ("Seine Sunset River Cruise", 48.8580, 2.2950, "leisure", 25.0),
            ("Champs-Élysées & Arc de Triomphe", 48.8738, 2.2950, "attraction", 16.0),
            ("Latin Quarter Bistro & Jazz Club", 48.8510, 2.3450, "dining", 45.0),
            ("Palace of Versailles Day Excursion", 48.8049, 2.1204, "attraction", 32.0),
        ],
    },
    "tokyo": {
        "lat": 35.6762,
        "lng": 139.6503,
        "country": "Japan",
        "highlights": [
            ("Senso-ji Temple & Asakusa Nakamise", 35.7148, 139.7967, "attraction", 0.0),
            ("Shibuya Crossing & Hachiko Statue", 35.6595, 139.7004, "sightseeing", 0.0),
            ("Tsukiji Outer Market Fresh Sushi", 35.6655, 139.7708, "dining", 35.0),
            ("Meiji Shrine & Yoyogi Park", 35.6764, 139.6993, "attraction", 0.0),
            ("Shinjuku Omoide Yokocho Izakaya Crawl", 35.6938, 139.7001, "dining", 40.0),
            ("Akihabara Electric Town & Arcade", 35.6983, 139.7731, "leisure", 15.0),
            ("teamLab Planets Immersive Digital Art", 35.6517, 139.7897, "attraction", 38.0),
            ("Roppongi Hills Mori Sky Deck", 35.6605, 139.7292, "sightseeing", 22.0),
        ],
    },
    "rome": {
        "lat": 41.9028,
        "lng": 12.4964,
        "country": "Italy",
        "highlights": [
            ("Colosseum & Roman Forum", 41.8902, 12.4922, "attraction", 24.0),
            ("Vatican Museums & Sistine Chapel", 41.9067, 12.4534, "attraction", 30.0),
            ("Pantheon & Piazza Navona", 41.8986, 12.4769, "attraction", 5.0),
            ("Trevi Fountain & Spanish Steps", 41.9009, 12.4833, "attraction", 0.0),
            ("Trastevere Artisan Trattoria Dinner", 41.8887, 12.4697, "dining", 38.0),
            ("Borghese Gallery & Villa Gardens", 41.9142, 12.4922, "attraction", 20.0),
        ],
    },
    "new york": {
        "lat": 40.7128,
        "lng": -74.0060,
        "country": "United States",
        "highlights": [
            ("Central Park Stroll & Bethesda Terrace", 40.7829, -73.9654, "leisure", 0.0),
            ("Metropolitan Museum of Art", 40.7794, -73.9632, "attraction", 30.0),
            ("High Line & Chelsea Market Dining", 40.7480, -74.0048, "dining", 35.0),
            ("Broadway Musical Performance", 40.7590, -73.9845, "leisure", 120.0),
            ("Statue of Liberty & Ellis Island", 40.6892, -74.0445, "attraction", 26.0),
            ("DUMBO & Brooklyn Bridge Scenic Walk", 40.7033, -73.9897, "sightseeing", 0.0),
        ],
    },
    "bali": {
        "lat": -8.4095,
        "lng": 115.1889,
        "country": "Indonesia",
        "highlights": [
            ("Ubud Sacred Monkey Forest Sanctuary", -8.5190, 115.2630, "attraction", 8.0),
            ("Tegallalang Rice Terraces & Swing", -8.4340, 115.2810, "sightseeing", 12.0),
            ("Uluwatu Cliff Temple & Kecak Sunset Dance", -8.8290, 115.0849, "attraction", 15.0),
            ("Canggu Beachfront Sunset Warung & Seafood", -8.6500, 115.1300, "dining", 20.0),
            ("Seminyak Boutique Wellness & Balinese Spa", -8.6870, 115.1580, "leisure", 35.0),
        ],
    },
}


class AIGeneratorService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY

    def _determine_active_provider(self) -> str:
        provider = settings.AI_PROVIDER
        if provider == "fallback":
            return "fallback"
        if provider == "gemini" and self.gemini_key:
            return "gemini"
        if provider == "openai" and self.openai_key:
            return "openai"
        if provider == "anthropic" and self.anthropic_key:
            return "anthropic"

        # Auto detection
        if self.gemini_key:
            return "gemini"
        if self.openai_key:
            return "openai"
        if self.anthropic_key:
            return "anthropic"

        return "fallback"

    async def generate_itinerary(self, req: TripCreateRequest) -> TripItinerary:
        provider = self._determine_active_provider()
        print(f"DEBUG: provider is {provider}", flush=True)

        # Calculate dates and duration
        try:
            d_start = datetime.strptime(req.start_date, "%Y-%m-%d")
            d_end = datetime.strptime(req.end_date, "%Y-%m-%d")
            days_count = max(1, (d_end - d_start).days + 1)
        except Exception:
            d_start = datetime.utcnow()
            days_count = 3
            d_end = d_start + timedelta(days=2)

        # Attempt LLM if keys available
        if provider == "gemini":
            try:
                result = await self._generate_with_gemini(req, d_start, days_count)
                if result:
                    return ItineraryOptimizer.optimize_itinerary(result)
            except Exception as e:
                print(f"Gemini API error: {e}. Falling back to internal engine.")

        elif provider == "openai":
            try:
                result = await self._generate_with_openai(req, d_start, days_count)
                if result:
                    return ItineraryOptimizer.optimize_itinerary(result)
            except Exception as e:
                print(f"OpenAI API error: {e}. Falling back to internal engine.")

        # Default high-quality knowledge engine
        result = self._generate_with_knowledge_engine(req, d_start, days_count)
        return ItineraryOptimizer.optimize_itinerary(result)

    async def regenerate_day(
        self, trip: TripItinerary, req: DayRegenerateRequest
    ) -> TripItinerary:
        """
        Regenerates a single day within the itinerary based on user refinement prompts.
        """
        day_index = req.day_number - 1
        if day_index < 0 or day_index >= len(trip.days):
            raise ValueError(f"Day number {req.day_number} is out of bounds.")

        existing_day = trip.days[day_index]
        date_str = existing_day.date

        prompt_focus = req.refinement_prompt or "Provide a fresh exciting alternative schedule"
        pace = req.pace_override or "balanced"
        interests = req.interests_override or ["Sightseeing", "Food & Dining"]

        # If LLM available, query for refined day
        provider = self._determine_active_provider()
        if provider in ("gemini", "openai"):
            try:
                new_day = await self._regenerate_day_llm(
                    trip.destination,
                    req.day_number,
                    date_str,
                    prompt_focus,
                    pace,
                    interests,
                    trip.budget_tier,
                    trip.travel_style,
                )
                if new_day:
                    trip.days[day_index] = new_day
                    trip.updated_at = datetime.utcnow().isoformat()
                    return ItineraryOptimizer.optimize_itinerary(trip)
            except Exception as err:
                print(f"LLM Day regeneration error: {err}. Using algorithmic alternative.")

        # Algorithmic day alternative generator
        new_activities = self._build_alternative_day_activities(
            trip.destination,
            req.day_number,
            prompt_focus,
            pace,
            interests,
            trip.budget_tier,
            trip.travel_style,
        )

        new_day = DayPlan(
            day_number=req.day_number,
            date=date_str,
            theme=f"Curated {prompt_focus[:40]} Experience",
            summary=f"Customized itinerary focusing on {prompt_focus}. Crafted to maximize enjoyment and pacing.",
            estimated_daily_cost=sum(a.cost_estimate for a in new_activities),
            activities=new_activities,
        )

        trip.days[day_index] = new_day
        trip.updated_at = datetime.utcnow().isoformat()
        return ItineraryOptimizer.optimize_itinerary(trip)

    # =========================================================================
    # BUILT-IN KNOWLEDGE & HEURISTICS GENERATOR
    # =========================================================================

    def _generate_with_knowledge_engine(
        self, req: TripCreateRequest, start_date: datetime, duration_days: int
    ) -> TripItinerary:
        trip_id = f"trip_{uuid.uuid4().hex[:10]}"
        dest_clean = req.destination.strip().title()
        dest_lower = req.destination.lower()

        # Find city profile or use geographic synthesis
        city_info = None
        for key in CITY_KNOWLEDGE_BASE:
            if key in dest_lower:
                city_info = CITY_KNOWLEDGE_BASE[key]
                break

        base_lat = city_info["lat"] if city_info else 48.8566
        base_lng = city_info["lng"] if city_info else 2.3522
        country = city_info["country"] if city_info else "Global"

        tier_multipliers = {
            "backpacker": 0.5,
            "budget": 0.8,
            "moderate": 1.2,
            "luxury": 2.5,
            "ultra_luxury": 5.0,
        }
        multiplier = tier_multipliers.get(req.budget_tier.lower(), 1.0)

        # Style themes
        style_title_prefix = {
            "solo": "Solo Explorer's",
            "couple": "Romantic & Scenic",
            "group": "Epic Group Adventure in",
            "family": "Memorable Family Journey through",
            "business": "Executive & Leisure Blend in",
        }.get(req.travel_style.lower(), "Complete Guide to")

        title = f"{style_title_prefix} {dest_clean} ({duration_days} Days)"

        # Generate day-by-day plans
        days: List[DayPlan] = []
        themes = [
            ("Arrival, Icon Highlights & City Vistas", "Get your bearings, marvel at world-famous icons, and savor regional specialties."),
            ("Historic Quarters & Immersive Cultural Arts", "Wander through centuries-old districts, visit landmark museums, and enjoy authentic street cafes."),
            ("Scenic Viewpoints & Culinary Revelations", "Breathtaking panoramic viewpoints, local artisan markets, and unforgettable sunset dining."),
            ("Hidden Gems, Local Neighborhoods & Leisure", "Off-the-beaten-path hidden alleyways, serene gardens, and vibrant modern districts."),
            ("Nature Escapes & Day Excursion", "Explore stunning nearby coastal cliffs, majestic palaces, or natural trails."),
            ("Shopping, Artisan Boutiques & Farewell Night", "Collect unique keepsakes, visit trendy shopping lanes, and celebrate with a premier farewell dinner."),
            ("Relaxed Morning, Coffee Culture & Departure", "Indulge in a tranquil breakfast, last-minute photography, and seamless airport transit."),
        ]

        for i in range(duration_days):
            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            theme_idx = i % len(themes)
            day_theme, day_summary = themes[theme_idx]

            activities = self._build_activities_for_day(
                dest_clean,
                i + 1,
                req.travel_style,
                req.interests,
                req.pace,
                multiplier,
                base_lat,
                base_lng,
                city_info,
            )

            daily_cost = sum(a.cost_estimate for a in activities)

            days.append(
                DayPlan(
                    day_number=i + 1,
                    date=current_date,
                    theme=f"Day {i + 1}: {day_theme}",
                    summary=day_summary,
                    estimated_daily_cost=round(daily_cost, 2),
                    activities=activities,
                )
            )

        # Overview
        overview = (
            f"Tailored {duration_days}-day itinerary for {dest_clean} designed specifically for a "
            f"{req.travel_style} travel style at a {req.pace} pace. "
            f"Featuring {', '.join(req.interests[:3])} with optimized scheduling to eliminate decision fatigue "
            f"and guarantee smooth logistics."
        )

        packing_list = [
            "Comfortable walking shoes with good grip",
            "Universal travel power adapter & power bank",
            "Weather-appropriate layered clothing",
            "Lightweight rain jacket or compact umbrella",
            "Copies of travel insurance and reservations",
        ]
        if "Food & Dining" in req.interests:
            packing_list.append("Smart-casual evening attire for upscale dining")
        if "Adventure" in req.interests:
            packing_list.append("Refillable water bottle & activewear")

        insights = [
            f"Public transit in {dest_clean} is efficient: pick up a rechargeable travel card upon arrival.",
            "Book top museum and attraction tickets 7-14 days in advance to skip ticket queues.",
            "Tipping customs: check local guidelines as service charges are often included in dining checks.",
            "Keep emergency contact numbers and digital copies of your passport stored offline.",
        ]

        itinerary = TripItinerary(
            id=trip_id,
            title=title,
            destination=dest_clean,
            country=country,
            start_date=req.start_date,
            end_date=req.end_date,
            duration_days=duration_days,
            travel_style=req.travel_style,
            group_size=req.group_size,
            budget_tier=req.budget_tier,
            budget_breakdown=BudgetBreakdown(user_budget=req.budget_amount),
            overview=overview,
            packing_essentials=packing_list,
            local_insights=insights,
            days=days,
        )

        return itinerary

    def _build_activities_for_day(
        self,
        destination: str,
        day_num: int,
        travel_style: str,
        interests: List[str],
        pace: str,
        multiplier: float,
        base_lat: float,
        base_lng: float,
        city_info: Optional[dict],
    ) -> List[Activity]:
        activities = []
        is_relaxed = pace == "relaxed"
        is_fast = pace == "fast_paced"

        # Coordinates offset generator for realistic pins
        def get_coords(slot_i: int):
            lat_off = (slot_i * 0.008) - 0.015 + ((day_num * 0.005) % 0.03)
            lng_off = (slot_i * 0.009) - 0.012 + ((day_num * 0.006) % 0.03)
            return round(base_lat + lat_off, 4), round(base_lng + lng_off, 4)

        # 1. MORNING
        lat, lng = get_coords(1)
        morning_title = f"{destination} Heritage Walk & Landmark Sights"
        morning_desc = f"Kick off the morning exploring the historic heart of {destination}. Take in iconic architecture and vibrant morning street life."
        if city_info and len(city_info["highlights"]) >= day_num:
            item = city_info["highlights"][(day_num - 1) % len(city_info["highlights"])]
            morning_title = f"{item[0]}"
            morning_desc = f"Experience {item[0]}, one of the premier landmarks in {destination}."
            lat, lng = item[1], item[2]

        activities.append(
            Activity(
                id=f"act_{uuid.uuid4().hex[:8]}",
                title=morning_title,
                category="attraction",
                time_slot="morning",
                start_time="09:00 AM",
                end_time="11:30 AM",
                description=morning_desc,
                location=f"{destination} Central Quarter",
                lat=lat,
                lng=lng,
                cost_estimate=round(20.0 * multiplier, 2),
                transit_info="Head out via central metro or a brisk 10-min morning walk from your accommodation.",
                booking_tips="Arrive right around opening time to avoid long entry lines.",
            )
        )

        # 2. AFTERNOON - LUNCH & EXPLORATION
        lat2, lng2 = get_coords(2)
        lunch_title = f"Artisan Lunch at {destination} Bistro"
        lunch_desc = f"Savor authentic regional delicacies and handcrafted specialties popular with locals."
        activities.append(
            Activity(
                id=f"act_{uuid.uuid4().hex[:8]}",
                title=lunch_title,
                category="dining",
                time_slot="afternoon",
                start_time="12:00 PM",
                end_time="01:30 PM",
                description=lunch_desc,
                location=f"Old Town District, {destination}",
                lat=lat2,
                lng=lng2,
                cost_estimate=round(25.0 * multiplier, 2),
                transit_info="Short 5-min walk from your morning activity.",
                booking_tips="Opt for the lunch prix-fixe menu for extraordinary value.",
            )
        )

        # Afternoon main activity
        lat3, lng3 = get_coords(3)
        activities.append(
            Activity(
                id=f"act_{uuid.uuid4().hex[:8]}",
                title=f"{destination} Cultural Arts & Scenic Promenade",
                category="attraction",
                time_slot="afternoon",
                start_time="02:00 PM",
                end_time="04:30 PM",
                description=f"Delve into world-class art collections, historic squares, and picturesque views across {destination}.",
                location=f"Cultural Quarter, {destination}",
                lat=lat3,
                lng=lng3,
                cost_estimate=round(18.0 * multiplier, 2),
                transit_info="12-minute scenic transit or walk through pedestrian avenues.",
                booking_tips="Digital tickets on your smartphone are accepted for instant entry.",
            )
        )

        # If fast-paced or group, add afternoon tea / coffee stop
        if not is_relaxed:
            lat4, lng4 = get_coords(4)
            activities.append(
                Activity(
                    id=f"act_{uuid.uuid4().hex[:8]}",
                    title=f"Sunset Viewpoint & Artisan Coffee House",
                    category="leisure",
                    time_slot="evening",
                    start_time="05:00 PM",
                    end_time="06:30 PM",
                    description=f"Unwind with specialty coffee or local beverages while admiring golden-hour views of the skyline.",
                    location=f"Panoramic Overlook, {destination}",
                    lat=lat4,
                    lng=lng4,
                    cost_estimate=round(12.0 * multiplier, 2),
                    transit_info="10-minute walk or quick taxi up to the scenic overlook.",
                    booking_tips="Prime golden hour photography spot—have cameras ready.",
                )
            )

        # 3. EVENING - DINNER & NIGHTLIFE
        lat5, lng5 = get_coords(5)
        dinner_title = (
            f"Curated Candlelight Dinner in {destination}"
            if travel_style == "couple"
            else f"Vibrant Group Feast & Local Tasting Menu"
            if travel_style == "group"
            else f"Signature Dinner & Craft Cocktails at {destination} Tavern"
        )
        activities.append(
            Activity(
                id=f"act_{uuid.uuid4().hex[:8]}",
                title=dinner_title,
                category="dining",
                time_slot="evening",
                start_time="07:30 PM",
                end_time="09:30 PM",
                description=f"Enjoy a memorable dining experience featuring locally-sourced ingredients, wine pairings, and vibrant ambiance.",
                location=f"Gastronomy Lane, {destination}",
                lat=lat5,
                lng=lng5,
                cost_estimate=round(48.0 * multiplier, 2),
                transit_info="15-minute taxi or metro ride from afternoon venue.",
                booking_tips="Evening table reservations strongly recommended.",
            )
        )

        # Optional night activity for solo/group
        if travel_style in ("solo", "group") and not is_relaxed:
            lat6, lng6 = get_coords(6)
            activities.append(
                Activity(
                    id=f"act_{uuid.uuid4().hex[:8]}",
                    title=f"Illuminated Night Walk & Live Music Venue",
                    category="leisure",
                    time_slot="night",
                    start_time="10:00 PM",
                    end_time="11:30 PM",
                    description=f"Experience {destination} illuminated under the night stars with live acoustic performances or rooftop lounges.",
                    location=f"Nightlife Waterfront, {destination}",
                    lat=lat6,
                    lng=lng6,
                    cost_estimate=round(15.0 * multiplier, 2),
                    transit_info="Safe pedestrian promenade in central district.",
                    booking_tips="Entry is usually free before 10:30 PM.",
                )
            )

        return activities

    def _build_alternative_day_activities(
        self,
        destination: str,
        day_num: int,
        refinement_prompt: str,
        pace: str,
        interests: List[str],
        budget_tier: str,
        travel_style: str,
    ) -> List[Activity]:
        """Generate alternative activities focused on user refinement."""
        base_lat, base_lng = 48.8566, 2.3522
        for key in CITY_KNOWLEDGE_BASE:
            if key in destination.lower():
                base_lat = CITY_KNOWLEDGE_BASE[key]["lat"]
                base_lng = CITY_KNOWLEDGE_BASE[key]["lng"]
                break

        focus = refinement_prompt.lower()
        activities = []

        # Morning customized
        activities.append(
            Activity(
                id=f"act_alt_{uuid.uuid4().hex[:8]}",
                title=f"Bespoke Morning Discovery: {refinement_prompt[:30]}",
                category="attraction",
                time_slot="morning",
                start_time="09:30 AM",
                end_time="11:45 AM",
                description=f"Tailored experience specifically addressing '{refinement_prompt}'. Explore curated highlights in {destination} without rush.",
                location=f"{destination} Discovery Quarter",
                lat=round(base_lat + 0.005, 4),
                lng=round(base_lng - 0.004, 4),
                cost_estimate=25.0,
                transit_info="Centrally located, easy access via metro or rideshare.",
                booking_tips="Custom-selected to fulfill your preference update.",
            )
        )

        # Lunch customized
        activities.append(
            Activity(
                id=f"act_alt_{uuid.uuid4().hex[:8]}",
                title=f"Locally Recommended Food Discovery",
                category="dining",
                time_slot="afternoon",
                start_time="12:15 PM",
                end_time="01:45 PM",
                description=f"Savor dishes tailored to your tastes in a charming ambiance matching {travel_style} travel preferences.",
                location=f"Artisan Dining District, {destination}",
                lat=round(base_lat + 0.008, 4),
                lng=round(base_lng + 0.002, 4),
                cost_estimate=30.0,
                transit_info="8-minute walk from morning discovery venue.",
                booking_tips="Ask for the chef's seasonal recommendation.",
            )
        )

        # Afternoon customized
        activities.append(
            Activity(
                id=f"act_alt_{uuid.uuid4().hex[:8]}",
                title=f"Specialized Afternoon Experience",
                category="leisure" if "relax" in focus else "attraction",
                time_slot="afternoon",
                start_time="02:30 PM",
                end_time="05:00 PM",
                description=f"Immerse in unique activities tuned to: {refinement_prompt}.",
                location=f"Scenic Neighborhood, {destination}",
                lat=round(base_lat - 0.006, 4),
                lng=round(base_lng + 0.007, 4),
                cost_estimate=22.0,
                transit_info="Direct tram or short 10-minute taxi ride.",
                booking_tips="Ideal for uncrowded, personalized pacing.",
            )
        )

        # Evening customized
        activities.append(
            Activity(
                id=f"act_alt_{uuid.uuid4().hex[:8]}",
                title=f"Refined Evening Dining & Atmosphere",
                category="dining",
                time_slot="evening",
                start_time="07:30 PM",
                end_time="09:45 PM",
                description=f"Top-rated evening experience aligning with your trip refinement in {destination}.",
                location=f"Atmospheric Square, {destination}",
                lat=round(base_lat - 0.003, 4),
                lng=round(base_lng - 0.005, 4),
                cost_estimate=50.0,
                transit_info="Convenient return transit to key hotel areas.",
                booking_tips="Reserved for your updated itinerary.",
            )
        )

        return activities

    # =========================================================================
    # LIVE LLM PROVIDERS (GEMINI & OPENAI)
    # =========================================================================

    async def _generate_with_gemini(
        self, req: TripCreateRequest, start_date: datetime, duration_days: int
    ) -> Optional[TripItinerary]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        
        prompt = f"""
You are an expert AI Travel Planner. Generate a detailed, day-by-day travel itinerary for:
Destination: {req.destination}
Duration: {duration_days} days (from {req.start_date} to {req.end_date})
Travel Style: {req.travel_style}
Group Size: {req.group_size}
Budget Tier: {req.budget_tier} (target amount: ${req.budget_amount or 'flexible'})
Pace: {req.pace}
Interests: {', '.join(req.interests)}
Special Notes: {req.special_notes or 'none'}

Return ONLY valid JSON matching this schema:
{{
  "title": "string",
  "destination": "{req.destination}",
  "country": "string",
  "overview": "string",
  "packing_essentials": ["string"],
  "local_insights": ["string"],
  "days": [
    {{
      "day_number": 1,
      "date": "{req.start_date}",
      "theme": "string",
      "summary": "string",
      "estimated_daily_cost": 0.0,
      "activities": [
        {{
          "id": "act_1_1",
          "title": "string",
          "category": "attraction",
          "time_slot": "morning",
          "start_time": "09:00 AM",
          "end_time": "11:30 AM",
          "description": "string",
          "location": "string",
          "lat": 48.8566,
          "lng": 2.3522,
          "cost_estimate": 25.0,
          "transit_info": "string",
          "booking_tips": "string"
        }}
      ]
    }}
  ]
}}
Do NOT include markdown formatting or triple backticks. Return raw JSON only.
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096},
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
                parsed = json.loads(cleaned)

                trip_id = f"trip_{uuid.uuid4().hex[:10]}"
                return TripItinerary(
                    id=trip_id,
                    title=parsed.get("title", f"Trip to {req.destination}"),
                    destination=req.destination,
                    country=parsed.get("country", ""),
                    start_date=req.start_date,
                    end_date=req.end_date,
                    duration_days=duration_days,
                    travel_style=req.travel_style,
                    group_size=req.group_size,
                    budget_tier=req.budget_tier,
                    budget_breakdown=BudgetBreakdown(user_budget=req.budget_amount),
                    overview=parsed.get("overview", ""),
                    packing_essentials=parsed.get("packing_essentials", []),
                    local_insights=parsed.get("local_insights", []),
                    days=[DayPlan(**d) for d in parsed.get("days", [])],
                )
        return None

    async def _generate_with_openai(
        self, req: TripCreateRequest, start_date: datetime, duration_days: int
    ) -> Optional[TripItinerary]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        sys_msg = (
            "You are a professional travel planner. Generate structured travel itineraries "
            "strictly adhering to JSON schemas."
        )
        user_msg = f"""Generate a {duration_days}-day itinerary for {req.destination} from {req.start_date} to {req.end_date}.
Style: {req.travel_style}, Group Size: {req.group_size}, Budget: {req.budget_tier}, Pace: {req.pace}, Interests: {', '.join(req.interests)}.
Return raw JSON with title, destination, country, overview, packing_essentials, local_insights, and days (each with day_number, date, theme, summary, estimated_daily_cost, and activities [id, title, category, time_slot, start_time, end_time, description, location, lat, lng, cost_estimate, transit_info, booking_tips])."""

        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_text)
                trip_id = f"trip_{uuid.uuid4().hex[:10]}"
                return TripItinerary(
                    id=trip_id,
                    title=parsed.get("title", f"Trip to {req.destination}"),
                    destination=req.destination,
                    country=parsed.get("country", ""),
                    start_date=req.start_date,
                    end_date=req.end_date,
                    duration_days=duration_days,
                    travel_style=req.travel_style,
                    group_size=req.group_size,
                    budget_tier=req.budget_tier,
                    budget_breakdown=BudgetBreakdown(user_budget=req.budget_amount),
                    overview=parsed.get("overview", ""),
                    packing_essentials=parsed.get("packing_essentials", []),
                    local_insights=parsed.get("local_insights", []),
                    days=[DayPlan(**d) for d in parsed.get("days", [])],
                )
        return None

    async def _regenerate_day_llm(
        self,
        destination: str,
        day_num: int,
        date_str: str,
        focus: str,
        pace: str,
        interests: List[str],
        budget_tier: str,
        travel_style: str,
    ) -> Optional[DayPlan]:
        # Live LLM day re-generator when keys are provided
        prompt = f"""Regenerate Day {day_num} for a trip to {destination} on {date_str}.
User feedback/focus: {focus}
Pace: {pace}, Style: {travel_style}, Interests: {', '.join(interests)}, Budget: {budget_tier}.
Return JSON only:
{{
  "day_number": {day_num},
  "date": "{date_str}",
  "theme": "string",
  "summary": "string",
  "estimated_daily_cost": 0.0,
  "activities": [
    {{
      "id": "act_{day_num}_1",
      "title": "string",
      "category": "attraction",
      "time_slot": "morning",
      "start_time": "09:00 AM",
      "end_time": "11:30 AM",
      "description": "string",
      "location": "string",
      "lat": 0.0,
      "lng": 0.0,
      "cost_estimate": 20.0,
      "transit_info": "string",
      "booking_tips": "string"
    }}
  ]
}}"""
        if self.gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
                    parsed = json.loads(cleaned)
                    return DayPlan(**parsed)
        return None

    # =========================================================================
    # TRIP COPILOT Q&A
    # =========================================================================

    async def ask_copilot(
        self, question: str, destination: Optional[str] = None
    ) -> ChatQueryResponse:
        dest = destination or "your travel destination"
        q_lower = question.lower()

        # Context-aware intelligent answers
        if "pack" in q_lower or "clothes" in q_lower or "weather" in q_lower:
            answer = (
                f"For {dest}, we recommend bringing versatile layers, comfortable walking shoes "
                f"suitable for cobblestone streets and long days, a compact travel umbrella, a lightweight jacket, "
                f"and an international adapter plug. If visiting cultural or religious sites, bring clothing that covers shoulders and knees."
            )
            actions = ["View Packing Checklist", "Check 7-day Weather Forecast", "Review Luggage Limits"]
        elif "sim" in q_lower or "internet" in q_lower or "esim" in q_lower:
            answer = (
                f"For internet in {dest}, the most economical method is an Airalo or Holafly digital eSIM activated before departure. "
                f"Alternatively, physical tourist SIM cards are available at the airport arrivals terminal. Most cafes and hotels offer complimentary high-speed Wi-Fi."
            )
            actions = ["Compare eSIM Providers", "Download Offline Maps", "Airport Arrival Tips"]
        elif "tip" in q_lower or "money" in q_lower or "currency" in q_lower or "cash" in q_lower:
            answer = (
                f"In {dest}, contactless payment (Apple Pay, Google Pay, Visa/Mastercard) is widely accepted in most venues. "
                f"However, it is always wise to keep 40-50 local currency cash for street food stalls, lockers, or local taxis. "
                f"Tipping customs: check your bill for service charges, which are frequently included automatically."
            )
            actions = ["Find Zero-Fee ATMs", "Check Current Exchange Rate", "Tipping Etiquette Guide"]
        elif "safe" in q_lower or "emergency" in q_lower:
            answer = (
                f"{dest} is generally very safe for travelers. Keep normal city awareness regarding pickpockets in crowded transit hubs and tourist spots. "
                f"Save the local emergency number (112 in Europe, 911 in the Americas, 110/119 in Japan) and register your trip with your government embassy if traveling solo."
            )
            actions = ["View Emergency Numbers", "Share Itinerary with Friends", "Save Embassy Location"]
        else:
            answer = (
                f"Great question regarding {dest}! Based on your itinerary, planning ahead and taking advantage of early-morning hours "
                f"or pre-booked skip-the-line admissions will optimize your experience. Let me know if you would like me to adjust any activities, "
                f"regenerate a day's schedule, or optimize route transit times!"
            )
            actions = ["Regenerate Day Schedule", "Optimize Route Logistics", "Calculate Total Cost"]

        return ChatQueryResponse(answer=answer, suggested_actions=actions)


ai_generator = AIGeneratorService()
