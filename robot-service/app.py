"""
Mycosoft Embodiment - Robot Service
====================================
FastAPI service for controlling the Elephant Robotics myCobot 280.

Endpoints:
- GET  /api/v1/health       - Health check
- GET  /api/v1/status       - Detailed robot status
- POST /api/v1/motion/home  - Move to home position
- POST /api/v1/motion/move_joints - Move to specified angles
- POST /api/v1/motion/stop  - Stop movement
- POST /api/v1/safety/freeze - Emergency freeze
- POST /api/v1/safety/unfreeze - Release freeze

Author: Mycosoft Labs
Date: January 2026
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Add directories for imports
PROJECT_ROOT = Path(__file__).parent.parent
ROBOT_SERVICE_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(ROBOT_SERVICE_DIR))

from routers import health_router, motion_router, safety_router
from hardware import get_robot_adapter


def load_config() -> dict:
    """Load configuration from settings.yaml"""
    config_path = PROJECT_ROOT / "config" / "settings.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"Config not found at {config_path}, using defaults")
        return {
            "robot": {"port": "COM8", "baudrate": 115200, "mock_mode": True},
            "api": {
                "host": "0.0.0.0",
                "port": 8010,
                "cors_origins": ["http://localhost:3000"]
            }
        }


# Load configuration
config = load_config()
robot_config = config.get("robot", {})
api_config = config.get("api", {})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Initializes robot connection on startup,
    disconnects on shutdown.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🤖 MYCOSOFT EMBODIMENT - Robot Service Starting")
    logger.info("=" * 60)
    
    # Initialize robot adapter
    adapter = get_robot_adapter(
        port=robot_config.get("port", "COM8"),
        baudrate=robot_config.get("baudrate", 115200),
        mock_mode=robot_config.get("mock_mode", False)
    )
    
    # Attempt connection
    if adapter.connect():
        logger.success(f"✅ Connected to myCobot 280 on {adapter.port}")
    else:
        logger.warning(f"⚠️  Could not connect to robot - running in degraded mode")
    
    logger.info(f"🌐 API available at http://localhost:{api_config.get('port', 8010)}")
    logger.info(f"📖 Docs at http://localhost:{api_config.get('port', 8010)}/docs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down robot service...")
    adapter.disconnect()
    logger.info("👋 Robot service stopped")


# Create FastAPI app
app = FastAPI(
    title="Mycosoft Embodiment - Robot Service",
    description="""
## myCobot 280 Control API

Control interface for Elephant Robotics myCobot 280 robot arm.

### Features
- 🤖 Joint angle control
- 🏠 Home position command
- 🛑 Stop and emergency freeze
- 📊 Real-time status monitoring
- 🔒 Safety limits and workspace bounds

### Safety
- Speed limiting enforced
- Joint limits validated
- Emergency freeze available at `/api/v1/safety/freeze`
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_origins = api_config.get("cors_origins", ["http://localhost:3000"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(motion_router)
app.include_router(safety_router)


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Mycosoft Embodiment - Robot Service",
        "version": "1.0.0",
        "description": "Control interface for myCobot 280",
        "docs": "/docs",
        "health": "/api/v1/health",
        "status": "/api/v1/status"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=api_config.get("host", "0.0.0.0"),
        port=api_config.get("port", 8010),
        reload=True,
        log_level="info"
    )
