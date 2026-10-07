"""
Pydantic Schemas for Machine Learning Endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SimilarityRequest(BaseModel):
    query: str = Field(..., description="Query text to compare against candidate documents")
    documents: List[str] = Field(..., min_length=1, description="List of document texts to evaluate")


class SimilarityResultItem(BaseModel):
    document_index: int
    text: str
    similarity_score: float


class SimilarityResponse(BaseModel):
    algorithm: str = "TF-IDF + Cosine Similarity (scikit-learn)"
    query: str
    total_evaluated: int
    results: List[SimilarityResultItem]


class ClusterRequest(BaseModel):
    documents: List[str] = Field(..., min_length=2, description="List of document texts to cluster")
    num_clusters: int = Field(default=2, ge=1, le=10, description="Target cluster count K")


class ClusterGroup(BaseModel):
    cluster_id: int
    top_keywords: List[str]
    member_count: int
    documents: List[Dict[str, Any]]


class ClusterResponse(BaseModel):
    algorithm: str
    clusters_count: int
    clusters: List[ClusterGroup]
