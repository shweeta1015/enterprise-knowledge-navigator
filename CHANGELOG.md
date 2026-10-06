# Changelog

All notable changes to the **Enterprise Knowledge Navigator** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-06 (Sprint 1 Milestone)

### Added
- **Repository Architecture**: Initialized enterprise-grade continuous repository layout (`backend/`, `frontend/`, `data/`, `docs/`, `tests/`, `config/`, `evaluation/`).
- **Core Backend Framework**: Configured FastAPI application with asynchronous lifespan handlers, dynamic CORS middleware, and OpenAPI documentation endpoints (`/docs`, `/redoc`).
- **Configuration Management**: Created `backend.app.core.config.Settings` backed by `pydantic-settings` with type safety and automatic directory verification.
- **Environment Management**: Added `.env.example` with standard defaults and secure exclusion of `.env` in `.gitignore`.
- **Structured Logging System**: Implemented rotating file logging (`logs/app.log`) and formatted console logging with debug level control.
- **Relational Persistence**: Added SQLAlchemy connection engine and ORM declarative models (`DocumentRecord`, `SystemLogRecord`) for SQLite database (`data/knowledge_navigator.db`).
- **Health Probing API**: Added `/api/v1/health`, `/api/v1/system/info`, and `/api/v1/ping` endpoints verifying live database connectivity and storage directory status.
- **Frontend Dashboard**: Created modern single-page dashboard (`frontend/index.html`, `style.css`, `app.js`) mounted at `/app/` with live API probe metrics, timeline roadmap, and architecture blueprint.
- **Automated Test Suite**: Implemented pytest suite (`tests/test_foundation.py`) verifying all endpoints, DB connectivity, and static mounts.
- **Sprint 1 Report**: Published comprehensive milestone documentation in `docs/sprint-01.md`.
