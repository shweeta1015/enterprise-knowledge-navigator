# Enterprise Knowledge Navigator

> **Enterprise GraphRAG & Semantic Retrieval Platform**  
> *A production-grade, end-to-end intelligent retrieval and knowledge graph platform*

---

## 1. Project Overview

**Enterprise Knowledge Navigator** is a production-grade, end-to-end enterprise knowledge retrieval and synthesis system. It bridges dense vector semantic retrieval with structured knowledge graph traversal (GraphRAG) to eliminate hallucinations, preserve institutional relationships, and deliver grounded citations across complex organizational documents.

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

## 7. Platform Capabilities Roadmap

| Subsystem | Scope & Capability | Status |
|---|---|---|
| **Core Architecture & Health** | FastAPI, SQLite, Pydantic configuration, structured logging, UI | **COMPLETED** |
| **Document Ingestion** | Multi-format ingestion (PDF, DOCX, TXT), validation, metadata extraction | In Progress |
| **Chunking & Semantic Embeddings** | Recursive chunking, overlap control, dense embedding vectors | Planned |
| **Vector Search Engine** | Persistent vector store, top-K cosine similarity retrieval | Planned |
| **RAG Assistant Engine** | Grounded prompt synthesis, context injection, source citations | Planned |
| **Knowledge Graph Builder** | Automated entity & relationship extraction, graph persistence | Planned |
| **GraphRAG Fusion Engine** | Multi-hop reasoning, hybrid vector + graph context fusion | Planned |
| **Enterprise Security & RBAC** | Role-based access control, secure authentication, audit logging | Planned |
| **Evaluation & Monitoring** | Groundedness evaluation, retrieval latency & accuracy metrics | Planned |
| **Production Hardening** | Scalability optimizations, containerization, deployment readiness | Planned |
