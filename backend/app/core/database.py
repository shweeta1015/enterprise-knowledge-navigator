"""
Database connection and session handling.
Uses SQLAlchemy with SQLite for reliable local and persistent data management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


from sqlalchemy import text


def ensure_database_schema_upgrades(db_engine):
    """Safely verifies and adds any newly defined columns to existing tables without data loss."""
    if "sqlite" in settings.DATABASE_URL:
        with db_engine.connect() as conn:
            try:
                # Verify users columns
                res_users = conn.execute(text("PRAGMA table_info(users)"))
                user_cols = [row[1] for row in res_users.fetchall()]
                if user_cols and "phone_number" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(50)"))
                    conn.commit()
                if user_cols and "is_verified" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 1"))
                    conn.commit()

                # Verify documents columns for multi-tenant access control
                res_docs = conn.execute(text("PRAGMA table_info(documents)"))
                doc_cols = [row[1] for row in res_docs.fetchall()]
                if doc_cols and "owner_id" not in doc_cols:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN owner_id VARCHAR(36)"))
                    conn.commit()
                if doc_cols and "access_level" not in doc_cols:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN access_level VARCHAR(50) DEFAULT 'internal'"))
                    conn.commit()
                if doc_cols and "allowed_roles" not in doc_cols:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN allowed_roles VARCHAR(255)"))
                    conn.commit()
            except Exception:
                pass


def get_db():
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
