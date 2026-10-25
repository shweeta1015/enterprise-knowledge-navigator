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
    """Seeds default demo accounts for each role if no users exist and ENABLE_DEMO_ACCOUNTS is True."""
    if not settings.ENABLE_DEMO_ACCOUNTS:
        logger.info("Demo account seeding is disabled (ENABLE_DEMO_ACCOUNTS=False). Skipping automatic demo user creation.")
        return

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


def seed_initial_documents():
    """Seeds foundational enterprise documents, chunks, and graph entities if database is completely empty."""
    db = SessionLocal()
    try:
        from backend.app.models.document import DocumentRecord, ChunkRecord, EntityRecord, RelationRecord
        doc_count = db.query(DocumentRecord).count()
        if doc_count > 0:
            return

        logger.info("Database contains zero documents. Seeding foundational enterprise documents and graph entities...")
        now = datetime.now(timezone.utc)

        # Ensure raw docs dir exists
        settings.RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)

        docs_data = [
            {
                "id": "doc_f78ac181-d03",
                "filename": "Demo_Enterprise_Security_Policy.docx",
                "file_type": "docx",
                "file_size_bytes": 38313,
                "file_path": str(settings.RAW_DOCS_DIR / "doc_f78ac181-d03_Demo_Enterprise_Security_Policy.docx"),
                "status": "indexed",
                "page_count": 2,
                "chunk_count": 2,
                "entity_count": 11,
                "chunks": [{"id": "doc_f78ac181-d03_0", "chunk_index": 0, "page_number": 1, "content": "DEMO ENTERPRISE SECURITY POLICY Sample document for testing Enterprise Knowledge Navigator IMPORTANT: This is fictional demonstration content created only to test document upload, search, grounded answers, citations, and GraphRAG-style relational expansion. It is not a real company policy and should not be used as security advice. 1. Purpose and Scope This sample policy describes basic security requirements for ExampleCorp, a fictional company. It applies to employees and contractors who access ExampleCorp information systems. 2. Data Encryption ExampleCorp requires sensitive enterprise data stored on company-managed systems to be encrypted at rest using AES-256. Data sent across networks must be protected with TLS 1.2 or a newer version. Employees must not send sensitive company data through unapproved personal email accounts. 3. Encryption Key Management The Security Team owns encryption-key management. Production encryption keys must be rotated at least once every 90 days and immediately after suspected compromise. Access to production keys is restricted to specifically authorized security administrators. 4. Remote Work Employees working remotely must connect to internal company resources through the approved company VPN. Multi-factor authentication (MFA) is required for remote access. Employees must lock their screens when leaving their devices unattended and must not use public shared computers to access company systems. 5. Security Incident Reporting Employees must report suspected data exposure, lost company devices, phishing, or unauthorized access to the Security Team within 24 hours of discovery. The Security Team records the incident, assesses its severity, and coordinates the response. 6. Roles and Responsibilities Employees are responsible for following this policy and reporting suspected incidents. The Security Team maintains encryption requirements, manages encryption keys, and coordinates incident response. Security administrators manage access to production encryption keys. Managers ensure that team members know how to report incidents. 7. Document Handling Documents uploaded to the demonstration system should be fictional or approved for testing. Users should not upload real passwords, personal identity documents, confidential business records, or other sensitive information into a demo environment. 8. Quick Facts for Testing 9. Suggested Questions for the Knowledge Navigator What encryption standard must be used for enterprise data at rest? Which protocol protects data sent across networks? How often must production encryption keys be rotated? Who is responsible for encryption-key management? What must an employee use to access company resources remotely? How soon must a suspected security incident be reported? Who manages production encryption-key access? What are the responsibilities of the Security Team? Topic", "token_count": 400}, {"id": "doc_f78ac181-d03_1", "chunk_index": 1, "page_number": 2, "content": "| Requirement Encryption at rest | AES-256 Encryption in transit | TLS 1.2 or newer Encryption key rotation | At least every 90 days Remote access | Approved company VPN and MFA Incident reporting deadline | Within 24 hours of discovery Owner of key management | Security Team", "token_count": 48}],
                "entities": [{"id": "ent_doc_f78ac181-d03_9142911", "name": "Key Management The Security Team", "category": "ORG", "mention_count": 1, "source_context": "unapproved personal email accounts. 3. Encryption Key Management The Security Team owns encryption-key management. Production encryp"}, {"id": "ent_doc_f78ac181-d03_3033984", "name": "Security Team", "category": "ORG", "mention_count": 11, "source_context": "devices, phishing, or unauthorized access to the Security Team within 24 hours of discovery. The Security Team r"}, {"id": "ent_doc_f78ac181-d03_6407603", "name": "ExampleCorp", "category": "ORG", "mention_count": 3, "source_context": "policy describes basic security requirements for ExampleCorp, a fictional company. It applies to employees and"}, {"id": "ent_doc_f78ac181-d03_4528444", "name": "GraphRAG", "category": "TECH", "mention_count": 1, "source_context": "upload, search, grounded answers, citations, and GraphRAG-style relational expansion. It is not a real comp"}, {"id": "ent_doc_f78ac181-d03_287975", "name": "AES-256", "category": "TECH", "mention_count": 2, "source_context": "any-managed systems to be encrypted at rest using AES-256. Data sent across networks must be protected with"}, {"id": "ent_doc_f78ac181-d03_4641073", "name": "TLS 1.2", "category": "TECH", "mention_count": 2, "source_context": "Data sent across networks must be protected with TLS 1.2 or a newer version. Employees must not send sensi"}, {"id": "ent_doc_f78ac181-d03_8559147", "name": "VPN", "category": "TECH", "mention_count": 2, "source_context": "al company resources through the approved company VPN. Multi-factor authentication (MFA) is required fo"}, {"id": "ent_doc_f78ac181-d03_6685582", "name": "MFA", "category": "TECH", "mention_count": 2, "source_context": "pproved company VPN. Multi-factor authentication (MFA) is required for remote access. Employees must lo"}, {"id": "ent_doc_f78ac181-d03_3493261", "name": "Encryption Key Management", "category": "POLICY", "mention_count": 1, "source_context": "ta through unapproved personal email accounts. 3. Encryption Key Management The Security Team owns encryption-key management."}, {"id": "ent_doc_f78ac181-d03_3931131", "name": "Incident Reporting", "category": "POLICY", "mention_count": 1, "source_context": "computers to access company systems. 5. Security Incident Reporting Employees must report suspected data exposure, lo"}, {"id": "ent_doc_f78ac181-d03_6770862", "name": "Knowledge Navigator", "category": "PRODUCT", "mention_count": 2, "source_context": "ITY POLICY Sample document for testing Enterprise Knowledge Navigator IMPORTANT: This is fictional demonstration conten"}],
                "relations": [{"id": "rel_doc_f78ac181-d03_6508392", "source_entity": "ExampleCorp", "relation_type": "REQUIRES", "target_entity": "AES-256", "provenance_text": "Data Encryption ExampleCorp requires sensitive enterprise data stored on company-managed systems to be encrypted at rest using AES-256."}, {"id": "rel_doc_f78ac181-d03_2942364", "source_entity": "Data sent across networks", "relation_type": "PROTECTED_BY", "target_entity": "TLS 1.2", "provenance_text": "Data sent across networks must be protected with TLS 1.2 or a newer version."}, {"id": "rel_doc_f78ac181-d03_9080972", "source_entity": "Security Team", "relation_type": "OWNS", "target_entity": "Encryption-Key Management", "provenance_text": "Encryption Key Management The Security Team owns encryption-key management."}, {"id": "rel_doc_f78ac181-d03_2852366", "source_entity": "Security Team", "relation_type": "MAINTAINS", "target_entity": "Encryption Requirements", "provenance_text": "The Security Team maintains encryption requirements, manages encryption keys, and coordinates incident response."}, {"id": "rel_doc_f78ac181-d03_2873548", "source_entity": "Security Team", "relation_type": "MANAGES", "target_entity": "Encryption Keys", "provenance_text": "The Security Team maintains encryption requirements, manages encryption keys, and coordinates incident response."}, {"id": "rel_doc_f78ac181-d03_7713637", "source_entity": "Security Team", "relation_type": "COORDINATES", "target_entity": "Incident Response", "provenance_text": "The Security Team maintains encryption requirements, manages encryption keys, and coordinates incident response."}]
            },
            {
                "id": "doc_b20b7a0d-107",
                "filename": "test_governance_manual.docx",
                "file_type": "docx",
                "file_size_bytes": 14200,
                "file_path": str(settings.RAW_DOCS_DIR / "doc_b20b7a0d-107_test_governance_manual.docx"),
                "status": "indexed",
                "page_count": 1,
                "chunk_count": 1,
                "entity_count": 3,
                "chunks": [
                    {
                        "id": "doc_b20b7a0d-107_0",
                        "chunk_index": 0,
                        "page_number": 1,
                        "content": "Enterprise Data Governance Manual Dr. Marcus Brody directs the Enterprise Security Division. The Enterprise Security Division establishes governance policies for PostgreSQL databases, Redis caching layers, and Docker container deployments. Data Encryption Standards All enterprise data at rest must employ AES-256 encryption without exception. The Cloud Architecture Council conducts biannual vulnerability assessments and penetration audits. Production database access requires hardware multi-factor authentication. Role | Responsibility | Compliance Target Security Officer | Key rotation every 90 days | ISO 27001",
                        "token_count": 85
                    }
                ],
                "entities": [
                    {"id": "ent_doc_b20b7a0d-107_189882", "name": "Marcus Brody", "category": "PERSON", "mention_count": 1, "source_context": "Enterprise Data Governance Manual Dr. Marcus Brody directs the Enterprise Security Division."},
                    {"id": "ent_doc_b20b7a0d-107_1654182", "name": "PostgreSQL", "category": "TECH", "mention_count": 1, "source_context": "The Enterprise Security Division establishes governance policies for PostgreSQL databases, Redis caching layers, and Docker container deployments."},
                    {"id": "ent_doc_b20b7a0d-107_8128908", "name": "Docker", "category": "TECH", "mention_count": 1, "source_context": "governance policies for PostgreSQL databases, Redis caching layers, and Docker container deployments."}
                ],
                "relations": []
            },
            {
                "id": "doc_2468756b-7da",
                "filename": "test_ai_ethics.pdf",
                "file_type": "pdf",
                "file_size_bytes": 8400,
                "file_path": str(settings.RAW_DOCS_DIR / "doc_2468756b-7da_test_ai_ethics.pdf"),
                "status": "indexed",
                "page_count": 1,
                "chunk_count": 1,
                "entity_count": 1,
                "chunks": [
                    {
                        "id": "doc_2468756b-7da_0",
                        "chunk_index": 0,
                        "page_number": 1,
                        "content": "Enterprise AI Ethics and Operational Guidelines. Professor Elena Gilbert oversees the AI Ethics Board. The AI Ethics Board evaluates machine learning pipelines and deep neural models. Knowledge Navigator operates under AI Ethics Board supervision.",
                        "token_count": 36
                    }
                ],
                "entities": [
                    {"id": "ent_doc_2468756b-7da_461425", "name": "Knowledge Navigator", "category": "PRODUCT", "mention_count": 1, "source_context": "machine learning pipelines and deep neural models. Knowledge Navigator operates under AI Ethics Board supervision."}
                ],
                "relations": []
            },
            {
                "id": "doc_eaefc824-5b0",
                "filename": "architecture_overview.txt",
                "file_type": "txt",
                "file_size_bytes": 2500,
                "file_path": str(settings.RAW_DOCS_DIR / "doc_eaefc824-5b0_architecture_overview.txt"),
                "status": "indexed",
                "page_count": 1,
                "chunk_count": 1,
                "entity_count": 8,
                "chunks": [
                    {
                        "id": "doc_eaefc824-5b0_0",
                        "chunk_index": 0,
                        "page_number": 1,
                        "content": "Enterprise Knowledge Navigator Architecture Overview. Dr. Alice Vance leads the Artificial Intelligence Engineering Department. The Artificial Intelligence Engineering Department develops the Knowledge Navigator platform. Knowledge Navigator integrates with PostgreSQL and Docker for enterprise operations. Remote Work Policy: Employees are permitted to work remotely up to two days per week with manager approval. Health insurance benefits cover medical examinations, hospitalization, and prescription drugs.",
                        "token_count": 65
                    }
                ],
                "entities": [
                    {"id": "ent_doc_eaefc824-5b0_3997549", "name": "Alice Vance", "category": "PERSON", "mention_count": 1, "source_context": "Dr. Alice Vance leads the Artificial Intelligence Engineering Department."},
                    {"id": "ent_doc_eaefc824-5b0_4647946", "name": "Artificial Intelligence Engineering Department", "category": "ORG", "mention_count": 1, "source_context": "Dr. Alice Vance leads the Artificial Intelligence Engineering Department."},
                    {"id": "ent_doc_eaefc824-5b0_6616", "name": "The Artificial Intelligence Engineering Department", "category": "ORG", "mention_count": 1, "source_context": "The Artificial Intelligence Engineering Department develops the Knowledge Navigator platform."},
                    {"id": "ent_doc_eaefc824-5b0_1654182", "name": "PostgreSQL", "category": "TECH", "mention_count": 1, "source_context": "Knowledge Navigator integrates with PostgreSQL and Docker for enterprise operations."},
                    {"id": "ent_doc_eaefc824-5b0_8128908", "name": "Docker", "category": "TECH", "mention_count": 1, "source_context": "Knowledge Navigator integrates with PostgreSQL and Docker for enterprise operations."},
                    {"id": "ent_doc_eaefc824-5b0_3657640", "name": "Artificial Intelligence", "category": "TECH", "mention_count": 1, "source_context": "Dr. Alice Vance leads the Artificial Intelligence Engineering Department."},
                    {"id": "ent_doc_eaefc824-5b0_1190623", "name": "Remote Work Policy", "category": "POLICY", "mention_count": 1, "source_context": "Remote Work Policy: Employees are permitted to work remotely up to two days per week with manager approval."},
                    {"id": "ent_doc_eaefc824-5b0_461425", "name": "Knowledge Navigator", "category": "PRODUCT", "mention_count": 1, "source_context": "Enterprise Knowledge Navigator Architecture Overview."}
                ],
                "relations": [
                    {"id": "rel_doc_eaefc824-5b0_5127976", "source_entity": "Alice Vance", "relation_type": "MANAGES", "target_entity": "Artificial Intelligence Engineering Department"},
                    {"id": "rel_doc_eaefc824-5b0_270346", "source_entity": "Artificial Intelligence Engineering Department", "relation_type": "DEVELOPS", "target_entity": "Knowledge Navigator"},
                    {"id": "rel_doc_eaefc824-5b0_3546010", "source_entity": "Knowledge Navigator", "relation_type": "INTEGRATES_WITH", "target_entity": "PostgreSQL"}
                ]
            },
            {
                "id": "doc_88a1a8b0-1ae",
                "filename": "zero_text_scanned.pdf",
                "file_type": "pdf",
                "file_size_bytes": 0,
                "file_path": str(settings.RAW_DOCS_DIR / "doc_88a1a8b0-1ae_zero_text_scanned.pdf"),
                "status": "error",
                "page_count": 1,
                "chunk_count": 0,
                "entity_count": 0,
                "error_message": "Document contains 0 readable text characters (empty or scanned image without OCR text layer).",
                "chunks": [],
                "entities": [],
                "relations": []
            },
            {
                "id": "doc_e58b5a3d-8da",
                "filename": "blank_scanned_doc.pdf",
                "file_type": "pdf",
                "file_size_bytes": 0,
                "file_path": str(settings.RAW_DOCS_DIR / "doc_e58b5a3d-8da_blank_scanned_doc.pdf"),
                "status": "error",
                "page_count": 1,
                "chunk_count": 0,
                "entity_count": 0,
                "error_message": "No extractable text found in uploaded document.",
                "chunks": [],
                "entities": [],
                "relations": []
            }
        ]

        for d in docs_data:
            doc_rec = DocumentRecord(
                id=d["id"],
                filename=d["filename"],
                file_type=d["file_type"],
                file_size_bytes=d["file_size_bytes"],
                file_path=d["file_path"],
                content_hash=None,
                status=d["status"],
                page_count=d["page_count"],
                chunk_count=d["chunk_count"],
                entity_count=d["entity_count"],
                error_message=d.get("error_message"),
                created_at=now,
                updated_at=now
            )
            db.add(doc_rec)
            raw_path = Path(d["file_path"])
            if not raw_path.exists():
                try:
                    raw_content = "\n\n".join([c["content"] for c in d["chunks"]])
                    raw_path.write_text(raw_content, encoding="utf-8")
                except Exception:
                    pass

            for c in d["chunks"]:
                chunk_rec = ChunkRecord(
                    id=c["id"],
                    document_id=d["id"],
                    chunk_index=c.get("chunk_index", 0),
                    page_number=c.get("page_number", 1),
                    content=c.get("content", ""),
                    token_count=c.get("token_count", 0),
                    created_at=now
                )
                db.add(chunk_rec)

            for e in d["entities"]:
                ent_rec = EntityRecord(
                    id=e["id"],
                    document_id=d["id"],
                    name=e["name"],
                    category=e["category"],
                    mention_count=e.get("mention_count", 1),
                    source_context=e.get("source_context")
                )
                db.add(ent_rec)

            for r in d["relations"]:
                rel_rec = RelationRecord(
                    id=r["id"],
                    document_id=d["id"],
                    source_entity=r["source_entity"],
                    relation_type=r["relation_type"],
                    target_entity=r["target_entity"],
                    provenance_text=r.get("provenance_text")
                )
                db.add(rel_rec)

        db.commit()
        logger.info("Foundational enterprise documents, chunks, and graph entities seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding initial documents: {e}")
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
seed_initial_documents()

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
    seed_initial_documents()
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
