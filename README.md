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
- **Machine Learning & NLP Engine**: Scikit-Learn (TF-IDF Vectorization, Cosine Similarity, K-Means Clustering), NumPy, Pandas
- **Configuration & Validation**: Pydantic v2, Pydantic-Settings, Python-Dotenv
- **Relational Persistence**: SQLAlchemy, SQLite (production ready for PostgreSQL)
- **Document Storage**: Persistent structured filesystem (`data/raw`, `data/processed`, `data/vector_store`, `data/graph_store`)
- **Testing**: Pytest, Starlette TestClient, AnyIO
- **Frontend**: Clean Modern Responsive Vanilla HTML5 / CSS3 / ES6 (no complex build tool requirements, served directly by FastAPI StaticFiles)

---

## 4. Current State: System Foundation

The foundational platform architecture is operational:
- [x] Modular project layout and secure configuration management
- [x] Structured file & console rotating logging system
- [x] SQLAlchemy persistence layer with SQLite backing (`data/knowledge_navigator.db`)
- [x] Machine Learning Core Engine (`scikit-learn` TF-IDF vectorization, Cosine Similarity ranking, K-Means semantic clustering)
- [x] Verified persistent filesystem storage structures (`data/raw`, `data/processed`, `data/vector_store`, `data/graph_store`)
- [x] Live operational health probing endpoints (`/api/v1/health`, `/api/v1/system/info`, `/api/v1/ping`, `/api/v1/ml/similarity`, `/api/v1/ml/cluster`)
- [x] Administrative system console dashboard with interactive ML diagnostics mounted at `/app/`
- [x] Automated test suite verifying system foundation and machine learning pipeline integrity

---

## 5. Getting Started

### Prerequisites
- Python 3.11+ (Python 3.14 supported)
- Git

### Installation & Setup

1. **Navigate to the project root:**
   ```bash
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
