"""
Machine Learning Core Service for Enterprise Knowledge Navigator.
Implements foundational statistical NLP and unsupervised Machine Learning:
- TF-IDF Vectorization (scikit-learn TfidfVectorizer)
- Mathematical Cosine Similarity Matrix computation
- Unsupervised Semantic Clustering (scikit-learn KMeans)
- Automated Keyword and Feature Extraction
"""

from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

from backend.app.core.logging import logger


class MachineLearningEngine:
    """Core ML service performing vectorization, similarity metrics, and unsupervised clustering."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=500
        )
        logger.info("MachineLearningEngine initialized with scikit-learn TfidfVectorizer.")

    def compute_similarity(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        """
        Computes cosine similarity between a target query and candidate documents.
        Uses TF-IDF feature space representation.
        """
        if not documents:
            return []

        corpus = [query] + documents
        tfidf_matrix = self.vectorizer.fit_transform(corpus)

        # Query vector is at index 0, document vectors are from index 1 onward
        query_vec = tfidf_matrix[0:1]
        doc_vecs = tfidf_matrix[1:]

        # Compute cosine similarity: dot(A, B) / (norm(A) * norm(B))
        similarities = cosine_similarity(query_vec, doc_vecs).flatten()

        results = []
        for idx, (doc, score) in enumerate(zip(documents, similarities)):
            results.append({
                "document_index": idx,
                "text": doc,
                "similarity_score": round(float(score), 4)
            })

        # Rank documents by highest similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results

    def cluster_documents(self, documents: List[str], num_clusters: int = 2) -> Dict[str, Any]:
        """
        Groups document texts using scikit-learn KMeans unsupervised clustering.
        Extracts dominant terms per cluster centroid.
        """
        if len(documents) < num_clusters:
            num_clusters = max(1, len(documents))

        tfidf_matrix = self.vectorizer.fit_transform(documents)
        feature_names = np.array(self.vectorizer.get_feature_names_out())

        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
        kmeans.fit(tfidf_matrix)

        labels = kmeans.labels_.tolist()

        # Identify top descriptive keywords per cluster centroid
        clusters_info = []
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

        for i in range(num_clusters):
            top_keyword_indices = order_centroids[i, :4]
            top_keywords = [feature_names[ind] for ind in top_keyword_indices if ind < len(feature_names)]
            
            cluster_members = [
                {"index": idx, "text": documents[idx]}
                for idx, cluster_id in enumerate(labels)
                if cluster_id == i
            ]

            clusters_info.append({
                "cluster_id": i,
                "top_keywords": top_keywords,
                "member_count": len(cluster_members),
                "documents": cluster_members
            })

        return {
            "algorithm": "K-Means (Unsupervised Clustering)",
            "clusters_count": num_clusters,
            "clusters": clusters_info
        }


ml_engine = MachineLearningEngine()
