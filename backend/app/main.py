"""
FastAPI Application Entrypoint for Enterprise Knowledge Navigator.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import engine, Base, SessionLocal, ensure_database_schema_upgrades
from backend.app.core.security import get_password_hash
from backend.app.api.v1 import api_router

# Import models so Base metadata is populated
import backend.app.models.document
import backend.app.models.user
import backend.app.models.workspace_extras
from backend.app.models.user import UserRecord, RoleRecord
from backend.app.models.workspace_extras import CollectionRecord, NotificationRecord


def seed_initial_roles():
    """Seeds default built-in roles (Administrator, Knowledge Worker, Knowledge Analyst) if not present."""
    db = SessionLocal()
    try:
        existing_roles = {r.id: r for r in db.query(RoleRecord).all()}
        builtin_roles_data = [
            {
                "id": "admin",
                "name": "Administrator",
                "description": "Full platform administration, user provisioning, role governance, and system telemetry.",
                "permissions": [
                    "system_admin", "audit_logs", "system_health",
                    "doc_ingestion", "doc_deletion", "search_retrieval",
                    "qa_citations", "knowledge_graph", "evaluation",
                    "export_center", "profile_settings"
                ],
                "is_builtin": True
            },
            {
                "id": "knowledge_worker",
                "name": "Knowledge Worker",
                "description": "Enterprise user with document upload, hybrid search, grounded Q&A with citations, and personal workspace tools.",
                "permissions": [
                    "doc_ingestion", "doc_deletion", "search_retrieval",
                    "qa_citations", "profile_settings"
                ],
                "is_builtin": True
            },
            {
                "id": "analyst",
                "name": "Knowledge Analyst",
                "description": "Analytics specialist with access to knowledge graph visualization, evaluation benchmarks, and platform exports.",
                "permissions": [
                    "search_retrieval", "qa_citations", "knowledge_graph",
                    "evaluation", "export_center", "profile_settings"
                ],
                "is_builtin": True
            }
        ]
        updated = False
        for br in builtin_roles_data:
            if br["id"] not in existing_roles:
                new_role = RoleRecord(
                    id=br["id"],
                    name=br["name"],
                    description=br["description"],
                    is_builtin=True,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                new_role.set_permissions(br["permissions"])
                db.add(new_role)
                updated = True
        if updated:
            db.commit()
            logger.info("Built-in system roles (Admin, Worker, Analyst) verified and seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding initial roles: {e}")
        db.rollback()
    finally:
        db.close()


def seed_initial_accounts():
    """Seeds default demo accounts for each role if no users exist."""
    db = SessionLocal()
    try:
        user_count = db.query(UserRecord).count()
        if user_count == 0:
            logger.info("Seeding initial role-based accounts (Admin, Knowledge Worker, Analyst)...")
            default_accounts = [
                {
                    "id": "user_admin_001",
                    "email": "admin@eknavigator.com",
                    "full_name": "System Administrator",
                    "password": "Admin@123456",
                    "role": "admin",
                    "organization": "Enterprise AI Systems"
                },
                {
                    "id": "user_worker_002",
                    "email": "worker@eknavigator.com",
                    "full_name": "Alex Morgan",
                    "password": "Worker@123456",
                    "role": "knowledge_worker",
                    "organization": "Engineering & Operations"
                },
                {
                    "id": "user_analyst_003",
                    "email": "analyst@eknavigator.com",
                    "full_name": "Dr. Jordan Lee",
                    "password": "Analyst@123456",
                    "role": "analyst",
                    "organization": "Analytics & Research"
                }
            ]
            for acc in default_accounts:
                user = UserRecord(
                    id=acc["id"],
                    email=acc["email"],
                    full_name=acc["full_name"],
                    hashed_password=get_password_hash(acc["password"]),
                    role=acc["role"],
                    organization=acc["organization"],
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(user)
            db.commit()
            logger.info("Initial role accounts seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding default accounts: {e}")
        db.rollback()
    finally:
        db.close()


def seed_initial_workspace_data():
    """Seeds default collections and system notifications if empty."""
    db = SessionLocal()
    try:
        col_count = db.query(CollectionRecord).count()
        if col_count == 0:
            logger.info("Seeding initial enterprise collections...")
            default_cols = [
                {
                    "id": "col_sec_001",
                    "name": "Security & Governance",
                    "description": "Information security policies, encryption mandates, and compliance directives.",
                    "color": "#4F46E5",
                    "icon": "🛡️"
                },
                {
                    "id": "col_ops_002",
                    "name": "Operations & Protocols",
                    "description": "Operational manuals, infrastructure configurations, and system protocols.",
                    "color": "#0EA5E9",
                    "icon": "⚙️"
                },
                {
                    "id": "col_eng_003",
                    "name": "Engineering Standards",
                    "description": "Software architecture designs, coding standards, and deployment pipelines.",
                    "color": "#10B981",
                    "icon": "📐"
                }
            ]
            for c in default_cols:
                col = CollectionRecord(
                    id=c["id"],
                    name=c["name"],
                    description=c["description"],
                    color=c["color"],
                    icon=c["icon"],
                    created_at=datetime.now(timezone.utc)
                )
                db.add(col)
            db.commit()

        notif_count = db.query(NotificationRecord).count()
        if notif_count == 0:
            logger.info("Seeding initial notifications...")
            default_notifs = [
                {
                    "id": "notif_init_001",
                    "title": "Enterprise Knowledge Platform Ready",
                    "message": "All semantic retrieval services, D3.js Knowledge Graph, and evaluation suites are operational.",
                    "category": "system"
                },
                {
                    "id": "notif_init_002",
                    "title": "Security Policies Active",
                    "message": "Role-Based Access Control (Admin, Worker, Analyst) and token authorization are strictly enforced.",
                    "category": "security"
                }
            ]
            for n in default_notifs:
                notif = NotificationRecord(
                    id=n["id"],
                    title=n["title"],
                    message=n["message"],
                    category=n["category"],
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(notif)
            db.commit()
    except Exception as e:
        logger.error(f"Error seeding workspace data: {e}")
        db.rollback()
    finally:
        db.close()


# Ensure storage directories and DB schema tables exist
settings.ensure_directories_exist()
Base.metadata.create_all(bind=engine)
ensure_database_schema_upgrades(engine)
seed_initial_roles()
seed_initial_accounts()
seed_initial_workspace_data()

# Ensure vector index reflects only active database chunks
_db_init = SessionLocal()
try:
    from backend.app.services.vector_index import vector_index_service
    vector_index_service.sync_with_database(_db_init)
except Exception as e:
    logger.error(f"Error initializing vector index sync: {e}")
finally:
    _db_init.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for application initialization and shutdown."""
    logger.info("Initializing Enterprise Knowledge Navigator services...")
    settings.ensure_directories_exist()
    logger.info("Verifying/creating database tables...")
    Base.metadata.create_all(bind=engine)
    ensure_database_schema_upgrades(engine)
    logger.info("Database schemas verified.")
    seed_initial_accounts()
    seed_initial_workspace_data()
    _db = SessionLocal()
    try:
        from backend.app.services.vector_index import vector_index_service
        vector_index_service.sync_with_database(_db)
    except Exception as e:
        logger.error(f"Error syncing vector index during startup: {e}")
    finally:
        _db.close()
    yield
    logger.info("Enterprise Knowledge Navigator shutting down safely.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Knowledge Navigator - Real-World GraphRAG & Semantic Retrieval Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve Frontend static files if directory exists
frontend_path = settings.BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/login", include_in_schema=False)
@app.get("/signup", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
def serve_spa_pages(request: Request):
    """Serves the Single Page Application HTML shell for client-side routing."""
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return RedirectResponse(url="/")


@app.get("/style.css", include_in_schema=False)
def serve_root_css():
    """Direct root static route for frontend stylesheet."""
    css_file = frontend_path / "style.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    return Response(status_code=404)


@app.get("/app.js", include_in_schema=False)
def serve_root_js():
    """Direct root static route for frontend SPA script."""
    js_file = frontend_path / "app.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    return Response(status_code=404)


@app.get("/", summary="Root Redirect / Landing")
def read_root(request: Request):
    """
    Returns public JSON status when invoked by automated tests or API clients.
    Serves the public landing page to web browsers requesting text/html.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return RedirectResponse(url="/app/")
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "api_docs": "/docs",
        "api_v1_health": f"{settings.API_V1_STR}/health",
        "web_interface": "/"
    }
