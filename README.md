# 🤖 Mycosoft Embodiment

> Robot arm control system for Elephant Robotics myCobot 280

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Overview

Mycosoft Embodiment provides a Python-based control interface for the **Elephant Robotics myCobot 280** robot arm. It includes:

- **Bring-up Script** - Verify hardware connection and basic movement
- **Robot Service** - FastAPI REST API for robot control
- **Hardware Adapter** - Abstraction layer with mock mode support
- **Safety System** - Speed limits, joint bounds, and emergency freeze

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** installed
- **myCobot 280** connected via USB (COM8 on Windows)
- **pymycobot** library compatible with your robot firmware

### Installation

```powershell
# Clone the repository
git clone https://github.com/MycosoftLabs/mycosoft-embodiment.git
cd mycosoft-embodiment

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Verify Hardware Connection

```powershell
# Run the bring-up test (will use mock mode if no hardware)
python scripts/bringup_move_test.py
```

Expected output:
```
🤖 MYCOSOFT EMBODIMENT - Bring-up Move Test
============================================================
📋 Configuration:
   Port: COM8
   Mock Mode: False
   Safe Speed: 15%

🔌 Step 1: Connecting to myCobot 280...
✅ Connected to myCobot 280

📖 Step 2: Reading current joint angles...
   Current angles: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
✅ Joint angles read successfully

🎯 Step 3: Performing small safe movement...
   Moving J1 by +5 degrees
✅ Movement completed

🔄 Step 4: Returning to original position...
✅ Returned to original position

🛑 Step 5: Stopping cleanly...
✅ Robot stopped

🎉 BRING-UP TEST COMPLETE
```

### Start the Robot Service

```powershell
# Start FastAPI server
cd robot-service
python app.py
```

The service will be available at:
- **API:** http://localhost:8010
- **Docs:** http://localhost:8010/docs
- **OpenAPI:** http://localhost:8010/openapi.json

---

## 📡 API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/status` | Detailed robot status |

### Motion Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/motion/home` | Move to home position |
| POST | `/api/v1/motion/move_joints` | Move to joint angles |
| POST | `/api/v1/motion/stop` | Stop movement |

### Safety

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/safety/freeze` | 🚨 Emergency freeze |
| POST | `/api/v1/safety/unfreeze` | Release freeze |
| GET | `/api/v1/safety/status` | Freeze status |

### Example: Move Joints

```bash
curl -X POST "http://localhost:8010/api/v1/motion/move_joints" \
  -H "Content-Type: application/json" \
  -d '{"angles": [10, 0, 0, 0, 0, 0], "speed": 20}'
```

---

## ⚙️ Configuration

Edit `config/settings.yaml`:

```yaml
robot:
  port: "COM8"          # Serial port
  baudrate: 115200      # Baud rate
  mock_mode: false      # Set true for testing without hardware

safety:
  max_speed: 50         # Maximum speed (deg/s)
  speed_limit_percent: 30  # Current limit (%)
  joint_limits:
    j1: [-165, 165]     # Joint 1 limits (degrees)
    # ... other joints
```

---

## 🛡️ Safety Features

### Speed Limiting
All movement commands are limited to `max_speed * speed_limit_percent / 100`

### Joint Limits
Angles are automatically clamped to safe ranges

### Emergency Freeze
Call `/api/v1/safety/freeze` to immediately stop and lock all movement

```bash
# Emergency freeze
curl -X POST "http://localhost:8010/api/v1/safety/freeze"

# Resume after verifying safety
curl -X POST "http://localhost:8010/api/v1/safety/unfreeze"
```

---

## 📁 Project Structure

```
mycosoft-embodiment/
├── config/
│   └── settings.yaml       # Configuration file
├── docs/
│   └── EMBODIMENT_AGENT.md # Agent role documentation
├── robot-service/
│   ├── app.py              # FastAPI application
│   ├── hardware/
│   │   ├── __init__.py
│   │   └── mycobot_adapter.py  # Hardware abstraction
│   └── routers/
│       ├── __init__.py
│       ├── health.py       # Health endpoints
│       ├── motion.py       # Motion endpoints
│       └── safety.py       # Safety endpoints
├── scripts/
│   └── bringup_move_test.py  # Hardware verification
├── requirements.txt
└── README.md
```

---

## 🔧 Development

### Mock Mode

For development without hardware, set `mock_mode: true` in config:

```yaml
robot:
  mock_mode: true
```

Or the system automatically uses mock mode if `pymycobot` isn't installed.

### Running Tests

```powershell
pytest tests/ -v
```

### Logging

Logs are written to `logs/robot-service.log` (rotated daily).

---

## 🗺️ Roadmap

### Week 1 (Current)
- [x] Basic joint control via Python
- [x] FastAPI robot-service
- [x] Safety limits and freeze

### Week 2
- [ ] Gripper control endpoints
- [ ] Cartesian space movements
- [ ] Movement queue/sequencing

### Month 1
- [ ] Camera integration (vision endpoints)
- [ ] Pick-and-place primitives
- [ ] Integration with MYCA orchestrator

---

## 🐛 Troubleshooting

### "Connection failed" on COM8
1. Check Device Manager for correct COM port
2. Verify robot is powered on
3. Ensure no other software is using the port
4. Try unplugging and reconnecting USB

### "pymycobot not installed"
```powershell
pip install pymycobot
```

### Robot moves unexpectedly fast
Check `config/settings.yaml`:
```yaml
safety:
  speed_limit_percent: 30  # Lower this value
```

---

## 📜 License

MIT License - See LICENSE file for details.

---

## 🔗 Links

- [Elephant Robotics](https://www.elephantrobotics.com/)
- [pymycobot Documentation](https://github.com/elephantrobotics/pymycobot)
- [Mycosoft Labs](https://github.com/MycosoftLabs)

---

*Built with ❤️ by Mycosoft Labs - January 2026*
