# Enterprise Knowledge Navigator

> **A 60-Day Real-World Enterprise GraphRAG & Semantic Retrieval Platform**  
> *Developed continuously across 10 Sprints × 6 Days*

---

## 1. Project Overview

**Enterprise Knowledge Navigator** is a production-grade, end-to-end enterprise knowledge retrieval and synthesis system. It bridges dense vector semantic retrieval with structured knowledge graph traversal (GraphRAG) to eliminate hallucinations, preserve institutional relationships, and deliver grounded citations across complex organizational documents.

This repository is built continuously from Sprint 1 to Sprint 10 without mockups, hardcoded answers, or disconnected prototypes.

---

## 2. High-Level Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │      Frontend Single-Page Dashboard (Web)     │
                    │      (Overview, Roadmap, API Diagnostic, etc) │
                    └──────────────────────┬───────────────────────┘
                                           │  REST / OpenAPI v3
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │         FastAPI Backend Application          │
                    │   - Config / Lifespan / Structured Logging   │
                    │   - Document ETL & Ingestion Controller      │
                    │   - Vector Search & Semantic Engine          │
                    │   - Knowledge Graph Extractor & Cypher Store │
                    │   - Hybrid Fusion & Context Synthesis (RAG)  │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────┴───────────────────────┐
                    │                 Persistence Layer            │
                    │  - SQLite / Relational DB (Metadata & Logs)  │
                    │  - Persistent Document Storage (Raw/Cleaned) │
                    │  - Vector Index Storage                      │
                    │  - Knowledge Graph Triple Store              │
                    └──────────────────────────────────────────────┘
```

---

## 3. Technology Stack

- **Backend Framework**: Python 3.14+, FastAPI, Uvicorn
- **Configuration & Validation**: Pydantic v2, Pydantic-Settings, Python-Dotenv
- **Relational Persistence**: SQLAlchemy, SQLite (production ready for PostgreSQL)
- **Document Storage**: Persistent structured filesystem (`data/raw`, `data/processed`, `data/vector_store`, `data/graph_store`)
- **Testing**: Pytest, Starlette TestClient, AnyIO
- **Frontend**: Clean Modern Responsive Vanilla HTML5 / CSS3 / ES6 (no complex build tool requirements, served directly by FastAPI StaticFiles)

---

## 4. Current Milestone: Sprint 1 (Foundation)

Sprint 1 delivers the production-ready foundation:
- [x] Structured modular project layout
- [x] Git repository initialization and `.gitignore` preventing secret leaks
- [x] Pydantic-Settings environment loading from `.env` with template `.env.example`
- [x] Structured file & console rotating logging system
- [x] SQLAlchemy persistence models (`DocumentRecord`, `SystemLogRecord`)
- [x] Live operational health checks (`/api/v1/health`, `/api/v1/system/info`, `/api/v1/ping`)
- [x] Interactive web dashboard mounted at `/app/`
- [x] Complete automated test coverage passing 100%

---

## 5. Getting Started

### Prerequisites
- Python 3.11+ (Python 3.14 supported)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shweeta1015/enterprise-knowledge-navigator.git
   cd enterprise-knowledge-navigator
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   python run.py
   ```

5. **Access services:**
   - **Interactive Web App**: [http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/)
   - **Swagger OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Health Check Probe**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 6. Running Tests

Execute the automated test suite:
```bash
pytest tests -v
```

---

## 7. Development Roadmap (10 Sprints × 6 Days)

| Sprint | Days | Focus Area | Status |
|---|---|---|---|
| **Sprint 1** | Days 1–6 | Project Foundation & Architecture | **COMPLETED** |
| **Sprint 2** | Days 7–12 | Real Document Ingestion (PDF, DOCX, TXT) | *Next* |
| **Sprint 3** | Days 13–18 | Chunking Strategy & Embedding Pipeline | Planned |
| **Sprint 4** | Days 19–24 | Vector Database & Semantic Search | Planned |
| **Sprint 5** | Days 25–30 | Real Grounded RAG Assistant | Planned |
| **Sprint 6** | Days 31–36 | Real Knowledge Graph Construction | Planned |
| **Sprint 7** | Days 37–42 | Real GraphRAG Hybrid Fusion Engine | Planned |
| **Sprint 8** | Days 43–48 | Enterprise Security, RBAC & Audit Trails | Planned |
| **Sprint 9** | Days 49–54 | Evaluation Framework & Polished UI | Planned |
| **Sprint 10** | Days 55–60 | Hardening, Production Deployment & Release v1.0.0 | Planned |
