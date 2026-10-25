import math
from typing import List
from ..models.schemas import TripItinerary, DayPlan, Activity, BudgetBreakdown


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in km."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class ItineraryOptimizer:
    """
    Optimizes activity sequences, travel time estimates, and budget allocations.
    """

    @staticmethod
    def optimize_day_schedule(day: DayPlan) -> DayPlan:
        """
        Sort activities logically by time slot and calculate realistic transit info.
        """
        slot_order = {"morning": 1, "afternoon": 2, "evening": 3, "night": 4}
        day.activities.sort(key=lambda a: slot_order.get(a.time_slot.lower(), 5))

        # Recalculate transit info based on coordinates where available
        prev_act: Activity | None = None
        daily_cost = 0.0

        for act in day.activities:
            daily_cost += float(act.cost_estimate or 0.0)

            if prev_act and act.lat and act.lng and prev_act.lat and prev_act.lng:
                dist_km = haversine_distance_km(
                    prev_act.lat, prev_act.lng, act.lat, act.lng
                )
                if dist_km < 1.0:
                    transit = f"Quick {int(dist_km * 12 + 4)}-min stroll ({dist_km * 1000:.0f}m) from {prev_act.title}"
                elif dist_km < 4.0:
                    transit = f"Short {int(dist_km * 4 + 8)}-min metro / bike ride ({dist_km:.1f} km) from {prev_act.title}"
                else:
                    transit = f"Convenient {int(dist_km * 3 + 12)}-min transit or taxi ({dist_km:.1f} km) from {prev_act.title}"

                if not act.transit_info:
                    act.transit_info = transit
            elif not act.transit_info:
                act.transit_info = "Short commute / walking distance"

            prev_act = act

        day.estimated_daily_cost = round(daily_cost, 2)
        return day

    @staticmethod
    def recalculate_budget(
        itinerary: TripItinerary, user_budget: float | None = None
    ) -> BudgetBreakdown:
        """
        Aggregates costs by category and assesses budget adherence.
        """
        breakdown = BudgetBreakdown()
        target = user_budget if user_budget is not None else itinerary.budget_breakdown.user_budget
        breakdown.user_budget = target

        total_attractions = 0.0
        total_dining = 0.0
        total_transit = 0.0
        total_stays = 0.0
        total_misc = 0.0

        # Base accommodation estimates based on budget tier and duration
        tier_multipliers = {
            "backpacker": 35.0,
            "budget": 65.0,
            "moderate": 140.0,
            "luxury": 320.0,
            "ultra_luxury": 650.0,
        }
        stay_daily_rate = tier_multipliers.get(
            itinerary.budget_tier.lower(), 130.0
        )
        total_stays = stay_daily_rate * max(1, itinerary.duration_days - 1)

        for day in itinerary.days:
            for act in day.activities:
                cat = act.category.lower()
                cost = float(act.cost_estimate or 0.0)
                if cat in ("dining", "food", "restaurant"):
                    total_dining += cost
                elif cat in ("attraction", "sightseeing", "tour", "museum"):
                    total_attractions += cost
                elif cat in ("transit", "transportation", "flight", "train"):
                    total_transit += cost
                elif cat in ("accommodation", "hotel", "stay"):
                    total_stays += cost
                else:
                    total_misc += cost

        # Standard daily local transit allocation if missing
        if total_transit == 0.0:
            total_transit = max(15.0, itinerary.duration_days * 18.0)

        total_estimated = total_attractions + total_dining + total_stays + total_transit + total_misc

        breakdown.attractions = round(total_attractions, 2)
        breakdown.dining = round(total_dining, 2)
        breakdown.transit = round(total_transit, 2)
        breakdown.accommodations = round(total_stays, 2)
        breakdown.miscellaneous = round(total_misc, 2)
        breakdown.total_estimated_cost = round(total_estimated, 2)

        if target and target > 0:
            if total_estimated <= target:
                breakdown.status = "within_budget"
            elif total_estimated <= target * 1.15:
                breakdown.status = "slightly_over"
            else:
                breakdown.status = "over_budget"
        else:
            breakdown.status = "within_budget"

        return breakdown

    @classmethod
    def optimize_itinerary(cls, itinerary: TripItinerary) -> TripItinerary:
        """
        Run full optimization pass on days and budget.
        """
        for day in itinerary.days:
            cls.optimize_day_schedule(day)
        itinerary.budget_breakdown = cls.recalculate_budget(itinerary)
        return itinerary
