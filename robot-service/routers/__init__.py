"""
FastAPI routers for robot-service.
"""
from .health import router as health_router
from .motion import router as motion_router
from .safety import router as safety_router

__all__ = ["health_router", "motion_router", "safety_router"]
