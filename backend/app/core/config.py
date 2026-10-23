"""
Core Configuration Module for Enterprise Knowledge Navigator.
Loads settings from environment variables or .env file with validated types.
"""

from pathlib import Path
from typing import List, Union, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "Enterprise Knowledge Navigator"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8080

    # Security
    SECRET_KEY: str = "dev-secret-key-knowledge-navigator"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ENABLE_DEMO_ACCOUNTS: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DOCS_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DOCS_DIR: Path = BASE_DIR / "data" / "processed"
    VECTOR_STORE_DIR: Path = BASE_DIR / "data" / "vector_store"
    GRAPH_STORE_DIR: Path = BASE_DIR / "data" / "graph_store"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Database
    DATABASE_URL: str = "sqlite:///./data/knowledge_navigator.db"

    # AI Model Providers
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    EMBEDDING_PROVIDER: str = "huggingface"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # API Keys
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Email / SMTP Configuration for Password Recovery
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@eknavigator.com"
    SMTP_TLS: bool = True

    # SMS / Twilio Configuration for Phone OTP
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # OTP Security Settings
    OTP_EXPIRE_MINUTES: int = 10
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_ATTEMPTS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("BACKEND_PORT", mode="before")
    @classmethod
    def resolve_backend_port(cls, v: Any) -> int:
        import os
        port_env = os.environ.get("PORT")
        if port_env:
            try:
                return int(port_env)
            except ValueError:
                pass
        return int(v) if v is not None else 8000

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def resolve_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    def model_post_init(self, __context: Any) -> None:
        if self.ENVIRONMENT.lower() == "production":
            if "DEBUG" not in self.model_fields_set:
                self.DEBUG = False
            if "ENABLE_DEMO_ACCOUNTS" not in self.model_fields_set:
                self.ENABLE_DEMO_ACCOUNTS = False
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == "dev-secret-key-knowledge-navigator"
                or len(self.SECRET_KEY) < 32
                or "dev-secret" in self.SECRET_KEY.lower()
            ):
                raise ValueError(
                    "FATAL SECURITY CONFIGURATION: In production (ENVIRONMENT=production), "
                    "a cryptographically strong, non-default SECRET_KEY of at least 32 characters "
                    "must be provided via environment variables."
                )

        if isinstance(self.DATA_DIR, str):
            self.DATA_DIR = Path(self.DATA_DIR)
        if not self.DATA_DIR.is_absolute():
            self.DATA_DIR = (self.BASE_DIR / self.DATA_DIR).resolve()

        self.RAW_DOCS_DIR = self.DATA_DIR / "raw"
        self.PROCESSED_DOCS_DIR = self.DATA_DIR / "processed"
        self.VECTOR_STORE_DIR = self.DATA_DIR / "vector_store"
        self.GRAPH_STORE_DIR = self.DATA_DIR / "graph_store"

        if isinstance(self.LOG_DIR, str):
            self.LOG_DIR = Path(self.LOG_DIR)
        if not self.LOG_DIR.is_absolute():
            self.LOG_DIR = (self.BASE_DIR / self.LOG_DIR).resolve()

        if "sqlite" in self.DATABASE_URL.lower() and "knowledge_navigator.db" in self.DATABASE_URL:
            db_file = self.DATA_DIR / "knowledge_navigator.db"
            self.DATABASE_URL = f"sqlite:///{db_file.as_posix()}"

    def ensure_directories_exist(self) -> None:
        """Ensure all required persistent directories exist on startup."""
        for path in [
            self.DATA_DIR,
            self.RAW_DOCS_DIR,
            self.PROCESSED_DOCS_DIR,
            self.VECTOR_STORE_DIR,
            self.GRAPH_STORE_DIR,
            self.LOG_DIR
        ]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
