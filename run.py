"""
Launcher script for Enterprise Knowledge Navigator.
Usage:
    python run.py
"""

import uvicorn
from backend.app.core.config import settings

if __name__ == "__main__":
    print("==================================================")
    print(f"[*] Launching {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"[*] Backend & Frontend URL: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"[*] Interactive Swagger Docs: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/docs")
    print(f"[*] Web Application Interface: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/app/")
    print("==================================================")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
