"""
Mycosoft Embodiment - myCobot Hardware Adapter
===============================================
Provides a hardware abstraction layer for the Elephant Robotics myCobot 280.
Supports both real hardware and mock mode for development/testing.

Author: Mycosoft Labs
Date: January 2026
"""

import time
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
from loguru import logger

try:
    from pymycobot.mycobot import MyCobot
    PYMYCOBOT_AVAILABLE = True
except ImportError:
    PYMYCOBOT_AVAILABLE = False
    logger.warning("pymycobot not installed - mock mode only")


class RobotState(Enum):
    """Robot operational state"""
    DISCONNECTED = "disconnected"
    IDLE = "idle"
    MOVING = "moving"
    ERROR = "error"
    FROZEN = "frozen"  # Emergency freeze state


@dataclass
class JointLimits:
    """Joint angle limits in degrees"""
    j1: tuple = (-165, 165)
    j2: tuple = (-165, 165)
    j3: tuple = (-165, 165)
    j4: tuple = (-165, 165)
    j5: tuple = (-165, 165)
    j6: tuple = (-175, 175)
    
    def validate(self, angles: List[float]) -> bool:
        """Check if angles are within limits"""
        limits = [self.j1, self.j2, self.j3, self.j4, self.j5, self.j6]
        for i, angle in enumerate(angles):
            if angle < limits[i][0] or angle > limits[i][1]:
                return False
        return True
    
    def clamp(self, angles: List[float]) -> List[float]:
        """Clamp angles to within limits"""
        limits = [self.j1, self.j2, self.j3, self.j4, self.j5, self.j6]
        return [
            max(limits[i][0], min(limits[i][1], angle))
            for i, angle in enumerate(angles)
        ]


@dataclass
class SafetyConfig:
    """Safety configuration parameters"""
    max_speed: int = 50  # Maximum speed percentage
    max_acceleration: int = 100  # Max accel deg/s^2
    speed_limit_percent: int = 30  # Current speed limit
    emergency_stop_time: float = 0.5  # Seconds to stop
    collision_detection: bool = True
    confirm_large_moves: bool = True
    large_move_threshold: float = 45.0  # Degrees
    joint_limits: JointLimits = field(default_factory=JointLimits)


class MyCobotAdapter:
    """
    Hardware abstraction adapter for myCobot 280.
    
    Provides a safe interface with:
    - Automatic mock mode when hardware unavailable
    - Speed limiting and safety checks
    - State management
    - Thread-safe operations
    - Emergency freeze capability
    """
    
    def __init__(
        self,
        port: str = "COM8",
        baudrate: int = 115200,
        mock_mode: bool = False,
        safety_config: Optional[SafetyConfig] = None
    ):
        self.port = port
        self.baudrate = baudrate
        self._mock_mode = mock_mode or not PYMYCOBOT_AVAILABLE
        self._safety = safety_config or SafetyConfig()
        
        self._robot: Optional[Any] = None
        self._state = RobotState.DISCONNECTED
        self._frozen = False
        self._lock = Lock()
        
        # Mock state
        self._mock_angles = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self._mock_gripper = 100  # 0-100 (100 = fully open)
        
        logger.info(f"MyCobotAdapter initialized (mock_mode={self._mock_mode})")
    
    @property
    def is_mock(self) -> bool:
        """Check if running in mock mode"""
        return self._mock_mode
    
    @property
    def state(self) -> RobotState:
        """Get current robot state"""
        return self._state
    
    @property
    def is_frozen(self) -> bool:
        """Check if robot is in emergency freeze state"""
        return self._frozen
    
    def connect(self) -> bool:
        """
        Connect to the robot.
        
        Returns:
            True if connection successful, False otherwise
        """
        with self._lock:
            if self._state != RobotState.DISCONNECTED:
                logger.warning("Already connected")
                return True
            
            try:
                if self._mock_mode:
                    logger.info(f"[MOCK] Connecting to {self.port}...")
                    time.sleep(0.1)  # Simulate connection delay
                else:
                    logger.info(f"Connecting to myCobot on {self.port}...")
                    self._robot = MyCobot(self.port, self.baudrate)
                    time.sleep(1)  # Wait for connection
                    self._robot.power_on()
                    time.sleep(0.5)
                
                self._state = RobotState.IDLE
                logger.success(f"Connected to myCobot 280 on {self.port}")
                return True
                
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                self._state = RobotState.ERROR
                return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the robot.
        
        Returns:
            True if disconnection successful
        """
        with self._lock:
            try:
                if self._robot and not self._mock_mode:
                    self._robot.power_off()
                
                self._state = RobotState.DISCONNECTED
                self._robot = None
                logger.info("Disconnected from myCobot")
                return True
                
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
                return False
    
    def get_angles(self) -> Optional[List[float]]:
        """
        Get current joint angles.
        
        Returns:
            List of 6 joint angles in degrees, or None if error
        """
        with self._lock:
            if self._state == RobotState.DISCONNECTED:
                logger.warning("Not connected")
                return None
            
            try:
                if self._mock_mode:
                    return self._mock_angles.copy()
                else:
                    angles = self._robot.get_angles()
                    if angles and len(angles) == 6:
                        return angles
                    return None
                    
            except Exception as e:
                logger.error(f"Failed to read angles: {e}")
                return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive robot status.
        
        Returns:
            Dictionary with status information
        """
        angles = self.get_angles()
        
        return {
            "connected": self._state != RobotState.DISCONNECTED,
            "state": self._state.value,
            "frozen": self._frozen,
            "mock_mode": self._mock_mode,
            "port": self.port,
            "angles": angles,
            "speed_limit": self._safety.speed_limit_percent,
            "safety": {
                "max_speed": self._safety.max_speed,
                "collision_detection": self._safety.collision_detection,
            }
        }
    
    def move_joints(
        self,
        angles: List[float],
        speed: Optional[int] = None,
        force: bool = False
    ) -> bool:
        """
        Move robot to specified joint angles.
        
        Args:
            angles: Target joint angles (6 values in degrees)
            speed: Movement speed (0-100), defaults to safety limit
            force: Skip safety checks (use with caution!)
        
        Returns:
            True if movement initiated successfully
        """
        with self._lock:
            # Safety checks
            if self._frozen:
                logger.error("🛑 Robot is FROZEN - cannot move")
                return False
            
            if self._state == RobotState.DISCONNECTED:
                logger.error("Not connected")
                return False
            
            if len(angles) != 6:
                logger.error(f"Invalid angles: expected 6, got {len(angles)}")
                return False
            
            # Apply speed limit
            max_allowed = int(self._safety.max_speed * self._safety.speed_limit_percent / 100)
            if speed is None:
                speed = max_allowed
            else:
                speed = min(speed, max_allowed)
            
            # Validate and clamp angles to limits
            if not force:
                if not self._safety.joint_limits.validate(angles):
                    logger.warning("Angles exceed limits, clamping...")
                    angles = self._safety.joint_limits.clamp(angles)
                
                # Check for large moves
                current = self.get_angles() or [0] * 6
                max_delta = max(abs(a - c) for a, c in zip(angles, current))
                
                if self._safety.confirm_large_moves and max_delta > self._safety.large_move_threshold:
                    logger.warning(f"Large movement detected ({max_delta:.1f}°)")
            
            try:
                self._state = RobotState.MOVING
                
                if self._mock_mode:
                    logger.info(f"[MOCK] Moving to {angles} at speed {speed}")
                    time.sleep(0.3)  # Simulate movement
                    self._mock_angles = angles.copy()
                else:
                    self._robot.send_angles(angles, speed)
                
                self._state = RobotState.IDLE
                logger.success(f"Movement complete: {angles}")
                return True
                
            except Exception as e:
                logger.error(f"Movement failed: {e}")
                self._state = RobotState.ERROR
                return False
    
    def move_home(self, speed: Optional[int] = None) -> bool:
        """
        Move robot to home position (all zeros).
        
        Args:
            speed: Movement speed (0-100)
        
        Returns:
            True if movement successful
        """
        home_position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        logger.info("Moving to home position...")
        return self.move_joints(home_position, speed)
    
    def stop(self) -> bool:
        """
        Stop robot movement immediately.
        
        Returns:
            True if stop command sent successfully
        """
        with self._lock:
            try:
                if self._mock_mode:
                    logger.info("[MOCK] Stop command sent")
                elif self._robot:
                    self._robot.stop()
                
                self._state = RobotState.IDLE
                logger.info("🛑 Robot stopped")
                return True
                
            except Exception as e:
                logger.error(f"Stop failed: {e}")
                return False
    
    def freeze(self) -> bool:
        """
        EMERGENCY FREEZE - Immediately stop and lock all movement.
        
        This is a safety function that:
        1. Sends immediate stop command
        2. Locks the robot from any further movement
        3. Requires explicit unfreeze() to resume
        
        Returns:
            True if freeze successful
        """
        logger.critical("🚨 EMERGENCY FREEZE ACTIVATED")
        
        with self._lock:
            self._frozen = True
            
            try:
                if self._mock_mode:
                    logger.info("[MOCK] Emergency freeze")
                elif self._robot:
                    self._robot.stop()
                    # Release servos to allow manual repositioning if needed
                    # self._robot.release_all_servos()
                
                self._state = RobotState.FROZEN
                logger.warning("Robot is now FROZEN - call unfreeze() to resume")
                return True
                
            except Exception as e:
                logger.error(f"Freeze command failed: {e}")
                return False
    
    def unfreeze(self) -> bool:
        """
        Release emergency freeze state.
        
        Returns:
            True if unfreeze successful
        """
        with self._lock:
            if not self._frozen:
                logger.info("Robot not frozen")
                return True
            
            self._frozen = False
            self._state = RobotState.IDLE
            logger.success("Robot unfrozen - movement enabled")
            return True


# Singleton instance
_robot_adapter: Optional[MyCobotAdapter] = None


def get_robot_adapter(
    port: str = "COM8",
    baudrate: int = 115200,
    mock_mode: bool = False,
    reinitialize: bool = False
) -> MyCobotAdapter:
    """
    Get or create the robot adapter singleton.
    
    Args:
        port: Serial port (e.g., "COM8")
        baudrate: Serial baudrate
        mock_mode: Force mock mode
        reinitialize: Force create new instance
    
    Returns:
        MyCobotAdapter instance
    """
    global _robot_adapter
    
    if _robot_adapter is None or reinitialize:
        _robot_adapter = MyCobotAdapter(
            port=port,
            baudrate=baudrate,
            mock_mode=mock_mode
        )
    
    return _robot_adapter
