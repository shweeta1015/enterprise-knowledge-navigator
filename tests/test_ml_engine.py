"""
Automated Tests for Machine Learning Engine and API Endpoints.
Verifies TF-IDF Vectorization, Cosine Similarity calculations, and K-Means clustering.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ml_engine import ml_engine

client = TestClient(app)


def test_ml_engine_direct_similarity():
    """Verify ML Engine direct cosine similarity calculation using scikit-learn."""
    query = "remote work and work from home policy"
    documents = [
        "Employees may work from home up to two days per week under the flexible remote work policy.",
        "The company annual financial revenue increased by fifteen percent this fiscal quarter.",
        "Server deployment guidelines require docker containers and kubernetes clusters."
    ]
    results = ml_engine.compute_similarity(query, documents)
    assert len(results) == 3
    # The first document (remote work) should have the highest similarity score
    assert results[0]["document_index"] == 0
    assert results[0]["similarity_score"] > 0.1
    # Financial or deployment docs should score lower
    assert results[0]["similarity_score"] > results[2]["similarity_score"]


def test_ml_engine_direct_clustering():
    """Verify ML Engine K-Means unsupervised clustering groups documents appropriately."""
    documents = [
        "Python machine learning neural networks deep learning models.",
        "FastAPI python rest api backend microservices endpoint.",
        "Tensorflow pytorch artificial intelligence machine learning training.",
        "Uvicorn async server backend request routing database connection."
    ]
    cluster_res = ml_engine.cluster_documents(documents, num_clusters=2)
    assert cluster_res["clusters_count"] == 2
    assert len(cluster_res["clusters"]) == 2
    assert cluster_res["algorithm"] == "K-Means (Unsupervised Clustering)"
    # Each cluster should have members
    assert sum(c["member_count"] for c in cluster_res["clusters"]) == 4


def test_api_similarity_endpoint():
    """Verify POST /api/v1/ml/similarity API endpoint returns structured ranking."""
    payload = {
        "query": "artificial intelligence models",
        "documents": [
            "Deep learning and artificial intelligence algorithms are used for natural language processing.",
            "Expense reimbursements must be submitted through the finance portal by month end."
        ]
    }
    response = client.post("/api/v1/ml/similarity", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluated"] == 2
    assert data["results"][0]["document_index"] == 0
    assert data["results"][0]["similarity_score"] > data["results"][1]["similarity_score"]


def test_api_cluster_endpoint():
    """Verify POST /api/v1/ml/cluster API endpoint returns clustered partitions and centroid terms."""
    payload = {
        "documents": [
            "Human resources policy on employee health insurance benefits.",
            "Vacation time and paid leave request procedure with HR.",
            "Database postgresql migration scripts and sql queries.",
            "Cloud infrastructure provisioning with terraform on AWS."
        ],
        "num_clusters": 2
    }
    response = client.post("/api/v1/ml/cluster", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["clusters_count"] == 2
    assert len(data["clusters"]) == 2
    assert "top_keywords" in data["clusters"][0]
