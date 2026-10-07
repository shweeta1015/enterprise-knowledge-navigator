"""
API Endpoints for Machine Learning Services.
Provides endpoints for TF-IDF Vectorization, Cosine Similarity, and K-Means Clustering.
"""

from fastapi import APIRouter, HTTPException, status
from backend.app.services.ml_engine import ml_engine
from backend.app.schemas.ml import (
    SimilarityRequest,
    SimilarityResponse,
    ClusterRequest,
    ClusterResponse
)
from backend.app.core.logging import logger

router = APIRouter()


@router.post("/similarity", response_model=SimilarityResponse, summary="Compute TF-IDF Cosine Similarity")
def compute_text_similarity(payload: SimilarityRequest):
    """
    Computes real cosine similarity scores using Scikit-Learn TF-IDF vectorization.
    Ranks input documents according to relevance to the query string.
    """
    try:
        ranked_results = ml_engine.compute_similarity(payload.query, payload.documents)
        return SimilarityResponse(
            query=payload.query,
            total_evaluated=len(payload.documents),
            results=ranked_results
        )
    except Exception as e:
        logger.error(f"Error computing text similarity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Machine learning vector calculation failed: {str(e)}"
        )


@router.post("/cluster", response_model=ClusterResponse, summary="Perform Unsupervised K-Means Clustering")
def perform_clustering(payload: ClusterRequest):
    """
    Performs unsupervised K-Means clustering across provided texts.
    Returns cluster groups and extracts dominant centroid keywords.
    """
    try:
        cluster_data = ml_engine.cluster_documents(payload.documents, payload.num_clusters)
        return ClusterResponse(**cluster_data)
    except Exception as e:
        logger.error(f"Error executing K-Means clustering: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"K-Means clustering failed: {str(e)}"
        )
