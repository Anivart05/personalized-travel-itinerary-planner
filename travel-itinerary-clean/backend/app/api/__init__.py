from .trips import router as trips_router
from .auth import router as auth_router
from .scenarios import router as scenarios_router

__all__ = ["trips_router", "auth_router", "scenarios_router"]
