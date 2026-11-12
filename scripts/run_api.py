"""Launch script for the BUTL-R FastAPI REST API Server (HACKNAUTS 2.0)."""

import os
import sys
from pathlib import Path

# Add project root to Python search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from app.api.server import create_app
from app.core.logger import get_logger

logger = get_logger("BUTL-R.API.Launcher")


def main():
    print("=" * 60)
    print("  BUTL-R REST API SERVER (FastAPI + Uvicorn)")
    print("  HACKNAUTS 2.0 - TheCruisers")
    print("=" * 60)
    print("  API Docs (Swagger UI): http://127.0.0.1:8000/docs")
    print("  Health Check:          http://127.0.0.1:8000/api/health")
    print("=" * 60)

    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
