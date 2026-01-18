"""
Health and Status Endpoints
===========================
Provides health checks and robot status information.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time

from hardware import get_robot_adapter

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str  # "healthy", "degraded", "unhealthy"
    service: str
    version: str
    timestamp: float
    robot_connected: bool
    mock_mode: bool


class StatusResponse(BaseModel):
    """Detailed status response"""
    connected: bool
    state: str
    frozen: bool
    mock_mode: bool
    port: str
    angles: Optional[List[float]]
    speed_limit: int
    safety: Dict[str, Any]
    uptime_seconds: float


# Service start time for uptime calculation
_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns basic health status of the robot service.
    """
    adapter = get_robot_adapter()
    
    # Determine health status
    if adapter.state.value == "error":
        status = "unhealthy"
    elif adapter.is_mock:
        status = "degraded"  # Running but in mock mode
    elif adapter.state.value == "disconnected":
        status = "degraded"
    else:
        status = "healthy"
    
    return HealthResponse(
        status=status,
        service="robot-service",
        version="1.0.0",
        timestamp=time.time(),
        robot_connected=adapter.state.value != "disconnected",
        mock_mode=adapter.is_mock
    )


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get detailed robot status.
    
    Returns comprehensive status including:
    - Connection state
    - Current joint angles
    - Safety settings
    - Freeze state
    """
    adapter = get_robot_adapter()
    status = adapter.get_status()
    
    return StatusResponse(
        connected=status["connected"],
        state=status["state"],
        frozen=status["frozen"],
        mock_mode=status["mock_mode"],
        port=status["port"],
        angles=status["angles"],
        speed_limit=status["speed_limit"],
        safety=status["safety"],
        uptime_seconds=time.time() - _start_time
    )
