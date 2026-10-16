"""
Production Configuration Generator for Enterprise Knowledge Navigator.
Generates .env.production with a secure 32-byte secret key, DEBUG=false, and ENVIRONMENT=production.
Never exposes or logs the generated secret value.
"""

import os
import secrets
from pathlib import Path


def generate_production_env():
    prod_env_path = Path(".env.production")
    prod_key = secrets.token_hex(32)

    content = f"""# ==============================================================================
# Enterprise Knowledge Navigator - Production Environment Configuration
# ==============================================================================

PROJECT_NAME="Enterprise Knowledge Navigator"
VERSION="0.1.0"
ENVIRONMENT="production"
DEBUG=false
API_V1_STR="/api/v1"
BACKEND_HOST="0.0.0.0"
BACKEND_PORT=8000
FRONTEND_PORT=8080

SECRET_KEY="{prod_key}"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

DATA_DIR="data"
RAW_DOCS_DIR="data/raw"
PROCESSED_DOCS_DIR="data/processed"
VECTOR_STORE_DIR="data/vector_store"
GRAPH_STORE_DIR="data/graph_store"
LOG_DIR="logs"

DATABASE_URL="sqlite:///./data/knowledge_navigator.db"

LLM_PROVIDER="groq"
LLM_MODEL="llama-3.3-70b-versatile"
EMBEDDING_PROVIDER="huggingface"
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"

GROQ_API_KEY=""
GEMINI_API_KEY=""
OPENAI_API_KEY=""

SMTP_HOST=""
SMTP_PORT=587
SMTP_USER=""
SMTP_PASSWORD=""
SMTP_FROM_EMAIL="noreply@eknavigator.com"
SMTP_TLS=true
"""
    with open(prod_env_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("[*] Successfully generated .env.production:")
    print("    - ENVIRONMENT=production")
    print("    - DEBUG=false")
    print("    - SECRET_KEY=<cryptographically-secure-random-256-bit-token>")
    print("    - Local development .env preserved separately.")


if __name__ == "__main__":
    generate_production_env()
