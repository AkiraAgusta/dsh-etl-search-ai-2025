"""
Start the CEH Datasets API server.

This script starts the FastAPI server using uvicorn.
"""

import uvicorn
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.config import get_settings


def main():
    """Start the API server."""
    settings = get_settings()
    
    print("=" * 70)
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print("=" * 70)
    print(f"Server: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"ReDoc: http://localhost:8000/redoc")
    print("=" * 70)
    print("Press CTRL+C to stop the server")
    print("=" * 70)
    
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()