"""
Pydantic Schemas for Document, Search, RAG, Graph, and Evaluation APIs.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# Document Schemas
class DocumentItem(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    page_count: int
    chunk_count: int
    entity_count: int
    owner_id: Optional[str] = None
    access_level: Optional[str] = "internal"
    allowed_roles: Optional[str] = None
    created_at: datetime
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    total_count: int
    documents: List[DocumentItem]


class DocumentDetailResponse(BaseModel):
    document: DocumentItem
    chunks_preview: List[Dict[str, Any]]
    entities_sample: List[Dict[str, Any]]


# Search Schemas
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    mode: str = Field(default="hybrid", description="retrieval mode: semantic, keyword, hybrid")
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    score: float
    retrieval_mode: str


class SearchResponse(BaseModel):
    query: str
    mode: str
    total_found: int
    results: List[SearchResultItem]


# RAG Assistant Schemas
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language question")
    enable_graphrag: bool = Field(default=True, description="Expand retrieval context using Knowledge Graph")
    top_k: int = Field(default=4, ge=1, le=10)
    document_filter: Optional[str] = None


class CitationItem(BaseModel):
    citation_id: int
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    relevance_score: float
    snippet: str
    verified: bool = True
    verified_match_ratio: float = 1.0


class AskResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    is_grounded: bool
    sources: List[CitationItem]
    graph_evidence: List[Dict[str, Any]]
    retrieval_mode: str
    searched_chunks_count: int
    verification_status: str = "verified"
    claim_support_rate: float = 1.0
    verified_claims_count: int = 0
    unverified_claims_count: int = 0
    contradictions_detected: List[str] = []
    synthesis_engine: str = "extractive_verified"


# Graph Schemas
class GraphNode(BaseModel):
    id: str
    label: str
    category: str
    mentions: int
    context: Optional[str] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    provenance: Optional[str] = None


class GraphResponse(BaseModel):
    node_count: int
    edge_count: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# Evaluation Schemas
class EvalRunResponse(BaseModel):
    run_id: str
    query_count: int
    precision_at_k: float
    recall_at_k: float
    mrr_score: float
    groundedness_score: float
    average_latency_ms: float
    k_depth: int
    total_indexed_chunks: int


class DashboardMetricsResponse(BaseModel):
    total_documents: int
    indexed_documents: int
    total_chunks: int
    total_entities: int
    total_relations: int
    storage_size_bytes: int
    latest_precision: Optional[float] = None
    latest_mrr: Optional[float] = None
    system_status: str
