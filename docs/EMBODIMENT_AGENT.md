# MYCA Embodiment Agent Role & Gating Rules

> **Document Version:** 1.0.0  
> **Date:** January 2026  
> **Author:** Mycosoft Labs  
> **Status:** Active

---

## Overview

The **MYCA Embodiment Agent** is the AI component responsible for physical robot control within the Mycosoft ecosystem. This document defines the role, responsibilities, and safety gating rules for AI-driven robot control.

---

## 🤖 Agent Role Definition

### Identity

| Property | Value |
|----------|-------|
| Agent Name | `MYCA-EMBODIMENT` |
| Agent Type | `robot_controller` |
| Hardware | Elephant Robotics myCobot 280 |
| Interface | Serial (COM8) via pymycobot |
| API Layer | FastAPI robot-service |

### Primary Responsibilities

1. **Motion Planning** - Translate high-level movement commands into safe joint trajectories
2. **Safety Enforcement** - Apply speed limits, joint bounds, and collision avoidance
3. **State Monitoring** - Track robot position, velocity, and health status
4. **Emergency Response** - Execute immediate freeze on safety violations

### Capabilities

- ✅ Read joint angles and robot status
- ✅ Execute joint-space movements
- ✅ Move to home position
- ✅ Emergency stop and freeze
- ⬜ Cartesian space movements (planned)
- ⬜ Gripper control (planned)
- ⬜ Camera integration (planned)
- ⬜ Pick-and-place sequences (planned)

---

## 🚦 Gating Rules

Gating rules define when the Embodiment Agent is permitted to take physical actions. These rules are **mandatory** and cannot be overridden by higher-level agents.

### Gate 1: Connection Gate

```
BEFORE ANY MOTION COMMAND:
  IF robot.state == DISCONNECTED:
    ATTEMPT connection with timeout
    IF connection fails:
      DENY motion
      LOG "Connection gate failed"
    ELSE:
      ALLOW motion
  ELSE:
    ALLOW motion
```

### Gate 2: Freeze Gate

```
BEFORE ANY MOTION COMMAND:
  IF robot.is_frozen == TRUE:
    DENY motion
    RESPOND with freeze status
    LOG "Freeze gate blocked command"
```

### Gate 3: Speed Limit Gate

```
BEFORE MOTION EXECUTION:
  effective_speed = MIN(requested_speed, max_speed * speed_limit_percent / 100)
  CLAMP effective_speed to [1, 100]
```

### Gate 4: Joint Limit Gate

```
BEFORE MOTION EXECUTION:
  FOR each joint angle:
    IF angle < joint_min OR angle > joint_max:
      IF force_mode:
        LOG warning
      ELSE:
        CLAMP angle to [joint_min, joint_max]
        LOG "Joint limit clamping applied"
```

### Gate 5: Large Movement Gate

```
BEFORE MOTION EXECUTION:
  max_delta = MAX(|target[i] - current[i]| for all joints)
  IF max_delta > LARGE_MOVE_THRESHOLD:
    IF confirm_large_moves == TRUE:
      LOG warning "Large movement detected"
      (Future: require explicit confirmation)
```

---

## 🛡️ Safety Hierarchy

Safety commands follow a strict priority hierarchy:

```
PRIORITY 1 (HIGHEST): Emergency Freeze
  - Immediately stops all motion
  - Locks all movement commands
  - Requires explicit unfreeze

PRIORITY 2: Stop Command
  - Halts current motion gracefully
  - Does not lock future commands

PRIORITY 3: Speed Limiting
  - Applied to all motion commands
  - Cannot be bypassed by user request

PRIORITY 4: Joint Clamping
  - Applied to all motion commands
  - Can be bypassed with force=True (logged)
```

---

## 📋 Command Permission Matrix

| Command | Mock Mode | Connected | Frozen | Result |
|---------|-----------|-----------|--------|--------|
| `GET /health` | ✅ | ✅ | ✅ | Always allowed |
| `GET /status` | ✅ | ✅ | ✅ | Always allowed |
| `POST /motion/home` | ✅ | ✅ | ❌ | Blocked if frozen |
| `POST /motion/move_joints` | ✅ | ✅ | ❌ | Blocked if frozen |
| `POST /motion/stop` | ✅ | ✅ | ✅ | Always allowed |
| `POST /safety/freeze` | ✅ | ✅ | ✅ | Always allowed |
| `POST /safety/unfreeze` | ✅ | ✅ | ✅ | Always allowed |

---

## 🔐 Authentication & Authorization

### Current Implementation (v1.0)

- **No authentication required** - Local development only
- Robot service runs on localhost:8010
- Access limited to local network

### Planned Implementation (v2.0)

- API key authentication for all motion endpoints
- Role-based access control:
  - `embodiment:read` - Status and health endpoints
  - `embodiment:move` - Motion commands
  - `embodiment:admin` - Safety override and configuration
- Integration with Mycosoft central auth service

---

## 🔄 State Machine

```
                    ┌─────────────────┐
                    │  DISCONNECTED   │
                    └────────┬────────┘
                             │ connect()
                             ▼
                    ┌─────────────────┐
         freeze()   │      IDLE       │◄──────┐
           ┌────────┤                 │       │ stop() or
           │        └────────┬────────┘       │ movement complete
           ▼                 │ move_*()       │
    ┌─────────────────┐      ▼                │
    │     FROZEN      │ ┌─────────────────┐   │
    │                 │ │     MOVING      │───┘
    └────────┬────────┘ └─────────────────┘
             │ unfreeze()      │ error
             ▼                 ▼
    ┌─────────────────┐ ┌─────────────────┐
    │      IDLE       │ │     ERROR       │
    └─────────────────┘ └─────────────────┘
```

---

## 📊 Logging Requirements

All physical actions MUST be logged:

```python
# Required log fields for motion commands
{
    "timestamp": "ISO8601",
    "command": "move_joints",
    "requested_angles": [j1, j2, j3, j4, j5, j6],
    "actual_angles": [j1, j2, j3, j4, j5, j6],  # After clamping
    "speed": 20,
    "gates_applied": ["speed_limit", "joint_clamp"],
    "result": "success" | "blocked" | "error",
    "duration_ms": 1234
}
```

---

## 🚨 Error Handling

| Error Type | Response | Recovery |
|------------|----------|----------|
| Connection Lost | Freeze robot, return 503 | Reconnect on next command |
| Invalid Angles | Clamp to limits, log warning | Continue with clamped values |
| Movement Timeout | Stop robot, return 504 | Require new command |
| Hardware Error | Freeze robot, return 500 | Manual intervention required |

---

## 📡 Integration with Other Agents

### Upstream (Commands FROM):
- **MYCA-ORCHESTRATOR** - High-level task commands
- **MYCA-VISION** (planned) - Visual servoing targets
- **Human Operator** - Direct API calls

### Downstream (Commands TO):
- **myCobot 280** - Physical hardware via pymycobot

### Status Reports TO:
- **MYCA-DASHBOARD** - Real-time status display
- **MycoBrain** - Telemetry logging
- **MINDEX** - Operational metrics

---

## 🔧 Configuration Reference

See `config/settings.yaml` for all configuration options.

Key safety parameters:
- `safety.max_speed` - Absolute maximum speed (default: 50)
- `safety.speed_limit_percent` - Current limit (default: 30%)
- `safety.joint_limits` - Per-joint angle limits
- `safety.large_move_threshold` - Warning threshold (default: 45°)

---

## 📝 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Jan 2026 | Initial document - Basic joint control |

---

## 🔗 Related Documents

- `README.md` - Project setup and usage
- `config/settings.yaml` - Configuration reference
- `robot-service/app.py` - API implementation
- `scripts/bringup_move_test.py` - Hardware verification

---

*This document is maintained by the Mycosoft Labs team.*
