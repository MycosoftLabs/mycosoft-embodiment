"""
Motion Control Endpoints
========================
Provides endpoints for robot movement control.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from hardware import get_robot_adapter

router = APIRouter(prefix="/api/v1/motion", tags=["motion"])


class MoveJointsRequest(BaseModel):
    """Request to move joints to specified angles"""
    angles: List[float] = Field(
        ..., 
        min_length=6, 
        max_length=6,
        description="Target joint angles in degrees [J1, J2, J3, J4, J5, J6]"
    )
    speed: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Movement speed (1-100%), defaults to safety limit"
    )


class MoveHomeRequest(BaseModel):
    """Request to move to home position"""
    speed: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Movement speed (1-100%)"
    )


class MotionResponse(BaseModel):
    """Standard motion response"""
    success: bool
    message: str
    current_angles: Optional[List[float]] = None


@router.post("/home", response_model=MotionResponse)
async def move_home(request: MoveHomeRequest = MoveHomeRequest()):
    """
    Move robot to home position.
    
    Home position is all joints at 0 degrees.
    Uses speed limiting for safety.
    """
    adapter = get_robot_adapter()
    
    if adapter.is_frozen:
        raise HTTPException(
            status_code=423,
            detail="Robot is FROZEN - call /api/v1/safety/unfreeze first"
        )
    
    # Connect if needed
    if adapter.state.value == "disconnected":
        if not adapter.connect():
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to robot"
            )
    
    success = adapter.move_home(request.speed)
    
    if success:
        return MotionResponse(
            success=True,
            message="Robot moved to home position",
            current_angles=adapter.get_angles()
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to move to home position"
        )


@router.post("/move_joints", response_model=MotionResponse)
async def move_joints(request: MoveJointsRequest):
    """
    Move robot to specified joint angles.
    
    Angles are specified in degrees for each joint [J1, J2, J3, J4, J5, J6].
    Movement is subject to:
    - Speed limiting (max speed based on safety config)
    - Joint limit clamping
    - Freeze state check
    """
    adapter = get_robot_adapter()
    
    if adapter.is_frozen:
        raise HTTPException(
            status_code=423,
            detail="Robot is FROZEN - call /api/v1/safety/unfreeze first"
        )
    
    # Connect if needed
    if adapter.state.value == "disconnected":
        if not adapter.connect():
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to robot"
            )
    
    success = adapter.move_joints(request.angles, request.speed)
    
    if success:
        return MotionResponse(
            success=True,
            message=f"Robot moved to {request.angles}",
            current_angles=adapter.get_angles()
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to execute movement"
        )


@router.post("/stop", response_model=MotionResponse)
async def stop_motion():
    """
    Stop robot movement immediately.
    
    This is a soft stop that halts current motion.
    For emergency situations, use /api/v1/safety/freeze instead.
    """
    adapter = get_robot_adapter()
    
    success = adapter.stop()
    
    if success:
        return MotionResponse(
            success=True,
            message="Robot stopped",
            current_angles=adapter.get_angles()
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to stop robot"
        )
