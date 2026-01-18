"""
Safety Control Endpoints
========================
Provides emergency safety controls for the robot.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from hardware import get_robot_adapter

router = APIRouter(prefix="/api/v1/safety", tags=["safety"])


class SafetyResponse(BaseModel):
    """Safety operation response"""
    success: bool
    message: str
    frozen: bool


@router.post("/freeze", response_model=SafetyResponse)
async def emergency_freeze():
    """
    🚨 EMERGENCY FREEZE
    
    Immediately stops all robot movement and locks the system.
    
    This is a critical safety function that:
    1. Sends immediate stop command to robot
    2. Locks all movement endpoints
    3. Requires explicit /unfreeze call to resume
    
    Use this in emergency situations when robot behavior is unexpected
    or poses a safety risk.
    """
    adapter = get_robot_adapter()
    
    success = adapter.freeze()
    
    return SafetyResponse(
        success=success,
        message="🚨 EMERGENCY FREEZE ACTIVATED - Robot locked" if success else "Freeze command failed",
        frozen=adapter.is_frozen
    )


@router.post("/unfreeze", response_model=SafetyResponse)
async def unfreeze():
    """
    Release emergency freeze state.
    
    ⚠️ CAUTION: Only call this after verifying:
    1. The emergency situation is resolved
    2. It is safe to resume robot operation
    3. The robot area is clear of personnel
    """
    adapter = get_robot_adapter()
    
    if not adapter.is_frozen:
        return SafetyResponse(
            success=True,
            message="Robot was not frozen",
            frozen=False
        )
    
    success = adapter.unfreeze()
    
    return SafetyResponse(
        success=success,
        message="Robot unfrozen - movement enabled" if success else "Unfreeze failed",
        frozen=adapter.is_frozen
    )


@router.get("/status", response_model=SafetyResponse)
async def safety_status():
    """
    Get current safety status.
    
    Returns whether the robot is in frozen state.
    """
    adapter = get_robot_adapter()
    
    return SafetyResponse(
        success=True,
        message="Robot is FROZEN" if adapter.is_frozen else "Robot is operational",
        frozen=adapter.is_frozen
    )
