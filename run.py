"""
Launcher script for Enterprise Knowledge Navigator.
Usage:
    python run.py
"""

import os
import uvicorn
from backend.app.core.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.BACKEND_PORT))
    host = os.environ.get(
        "BACKEND_HOST",
        "0.0.0.0" if os.environ.get("PORT") or settings.ENVIRONMENT.lower() == "production" else settings.BACKEND_HOST
    )
    print("==================================================")
    print(f"[*] Launching {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"[*] Backend & Frontend URL: http://{host}:{port}")
    print(f"[*] Interactive Swagger Docs: http://{host}:{port}/docs")
    print(f"[*] Web Application Interface: http://{host}:{port}/")
    print("==================================================")
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG
    )
