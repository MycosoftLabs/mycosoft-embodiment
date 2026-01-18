"""
Hardware abstraction layer for robot control.
"""
from .mycobot_adapter import MyCobotAdapter, get_robot_adapter

__all__ = ["MyCobotAdapter", "get_robot_adapter"]
