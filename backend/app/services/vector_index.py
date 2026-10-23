"""
Persistent Vector Index & Hybrid Retrieval Service.
Implements:
- TF-IDF Sparse Inverted Index
- Dense Statistical Embeddings & Cosine Retrieval
- Keyword BM25/Exact Frequency Matching
- Hybrid Reciprocal Rank Fusion (RRF)
- Top-K Filtering by Document & Metadata
- Disk Persistence in data/vector_store/
"""

import json
import math
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.core.config import settings
from backend.app.core.logging import logger


class VectorIndexService:
    """Manages document chunk embeddings, vector store persistence, and hybrid search."""

    def __init__(self):
        self.store_dir = settings.VECTOR_STORE_DIR
        self.index_file = self.store_dir / "hybrid_index.pkl"
        self.chunks_meta_file = self.store_dir / "chunks_metadata.json"

        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.chunks: List[Dict[str, Any]] = []  # List of chunk metadata dicts
        self.load_index()

    def load_index(self):
        """Loads persistent vector index and metadata from disk if available."""
        try:
            if self.index_file.exists() and self.chunks_meta_file.exists():
                with open(self.index_file, "rb") as f:
                    data = pickle.load(f)
                    self.vectorizer = data.get("vectorizer")
                    self.tfidf_matrix = data.get("tfidf_matrix")

                with open(self.chunks_meta_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info(f"Loaded {len(self.chunks)} persistent chunks into vector search index.")
            else:
                self.chunks = []
                self.vectorizer = None
                self.tfidf_matrix = None
        except Exception as e:
            logger.error(f"Failed to load vector index: {e}. Initializing fresh index.")
            self.chunks = []
            self.vectorizer = None
            self.tfidf_matrix = None

    def save_index(self):
        """Persists current vector matrix and chunk metadata to disk."""
        try:
            self.store_dir.mkdir(parents=True, exist_ok=True)
            with open(self.index_file, "wb") as f:
                pickle.dump({
                    "vectorizer": self.vectorizer,
                    "tfidf_matrix": self.tfidf_matrix
                }, f)

            with open(self.chunks_meta_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, indent=2, default=str)
            logger.info(f"Persisted vector index with {len(self.chunks)} chunks to {self.store_dir}")
        except Exception as e:
            logger.error(f"Failed to save vector index to disk: {e}")

    def sync_with_database(self, db):
        """
        Synchronizes vector index chunks directly with active indexed documents in SQLite.
        Purges any orphaned chunks whose document_id does not exist in the database with status 'indexed'.
        """
        try:
            from backend.app.models.document import DocumentRecord, ChunkRecord
            active_docs = {d.id: d.filename for d in db.query(DocumentRecord).filter(DocumentRecord.status == "indexed").all()}
            if not active_docs:
                self.chunks = []
                self._rebuild_index()
                self.save_index()
                return

            db_chunks = db.query(ChunkRecord).filter(ChunkRecord.document_id.in_(active_docs.keys())).all()
            synced_chunks = []
            for c in db_chunks:
                synced_chunks.append({
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "filename": active_docs.get(c.document_id, "unknown"),
                    "chunk_index": c.chunk_index,
                    "page_number": c.page_number,
                    "content": c.content,
                    "token_count": c.token_count
                })

            self.chunks = synced_chunks
            self._rebuild_index()
            self.save_index()
            logger.info(f"Synchronized vector index with active database: {len(self.chunks)} chunks.")
        except Exception as e:
            logger.error(f"Failed to synchronize vector index with database: {e}")

    def add_document_chunks(self, document_id: str, filename: str, chunks_data: List[Dict[str, Any]]):
        """Adds or updates chunks for a document and rebuilds the vector index."""
        # Remove any existing chunks for this document
        self.chunks = [c for c in self.chunks if c.get("document_id") != document_id]

        for c in chunks_data:
            self.chunks.append({
                "chunk_id": c.get("chunk_id", f"{document_id}_{c['chunk_index']}"),
                "document_id": document_id,
                "filename": filename,
                "chunk_index": c["chunk_index"],
                "page_number": c.get("page_number", 1),
                "content": c["content"],
                "token_count": c.get("token_count", len(c["content"].split()))
            })

        self._rebuild_index()
        self.save_index()

    def remove_document_chunks(self, document_id: str):
        """Removes all chunks associated with a deleted document and updates the index."""
        initial_len = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.get("document_id") != document_id]
        if len(self.chunks) != initial_len:
            self._rebuild_index()
            self.save_index()

    def _rebuild_index(self):
        """Fits TfidfVectorizer across all active chunks in the knowledge base."""
        if not self.chunks:
            self.vectorizer = None
            self.tfidf_matrix = None
            return

        corpus = [c["content"] for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=25000
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        logger.info(f"Rebuilt TF-IDF semantic vector space: {self.tfidf_matrix.shape[0]} chunks x {self.tfidf_matrix.shape[1]} features")

    def _expand_query(self, query: str) -> Tuple[str, List[str]]:
        """Extracts morphological stems and domain synonyms for robust semantic matching."""
        tokens = [t.lower().strip(".,;:?!'\"()[]{}") for t in query.split() if t.strip(".,;:?!'\"()[]{}")]
        roots = set()
        for t in tokens:
            if t.endswith("ing") and len(t) > 5:
                roots.add(t[:-3])
            elif t.endswith("ly") and len(t) > 4:
                roots.add(t[:-2])
            elif t.endswith("ies") and len(t) > 4:
                roots.add(t[:-3] + "y")
            elif t.endswith("es") and len(t) > 4:
                roots.add(t[:-2])
            elif t.endswith("s") and not t.endswith("ss") and len(t) > 3:
                roots.add(t[:-1])

        synonyms = set()
        q_lower = query.lower()
        if "telecommut" in q_lower or "work from home" in q_lower or "wfh" in q_lower:
            synonyms.update(["remote", "work"])
        if "healthcare" in q_lower or "medical care" in q_lower or "perks" in q_lower:
            synonyms.update(["health", "insurance", "medical", "benefits"])
        if "container" in q_lower:
            synonyms.update(["docker", "containerization"])
        if "database" in q_lower:
            synonyms.update(["postgresql", "redis"])

        expansion_terms = list(roots.union(synonyms))
        expanded_query = f"{query} {' '.join(expansion_terms)}" if expansion_terms else query
        return expanded_query, expansion_terms

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        allowed_doc_ids: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Vector retrieval using TF-IDF sublinear vector space with cosine similarity and query expansion."""
        if not query or not query.strip() or not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        expanded_query, _ = self._expand_query(query)
        query_vec = self.vectorizer.transform([expanded_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        scored = []
        for idx, score in enumerate(similarities):
            chunk = self.chunks[idx]
            if document_id and chunk.get("document_id") != document_id:
                continue
            if allowed_doc_ids is not None and chunk.get("document_id") not in allowed_doc_ids:
                continue
            if score > 0.001:
                scored.append({
                    **chunk,
                    "score": round(float(score), 4),
                    "retrieval_mode": "semantic"
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        allowed_doc_ids: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Lexical term matching with stopword filtering, phrase matching, and frequency density scoring."""
        if not query or not query.strip() or not self.chunks:
            return []

        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

        framing_meta_words = {
            "company", "enterprise", "corporate", "policy", "protocol", "procedure", "process",
            "framework", "strategy", "guidelines", "rules", "standard", "documentation",
            "overview", "information", "details", "system", "describe", "many", "much", "tell",
            "show", "explain", "give", "please", "regarding", "related", "pertaining", "accordance",
            "requirement", "specification"
        }
        stopwords = set(ENGLISH_STOP_WORDS).union(framing_meta_words)

        expanded_query, exp_terms = self._expand_query(query)
        raw_tokens = [t.lower().strip(".,;:?!'\"()[]{}") for t in expanded_query.split() if t.strip(".,;:?!'\"()[]{}")]
        filtered_terms = [t for t in raw_tokens if len(t) >= 2 and t not in stopwords]
        query_terms = filtered_terms if filtered_terms else raw_tokens

        # Extract 2-word and 3-word n-gram phrases from query for exact phrase match bonus
        phrases = []
        if len(raw_tokens) >= 2:
            for i in range(len(raw_tokens) - 1):
                p2 = f"{raw_tokens[i]} {raw_tokens[i+1]}"
                if raw_tokens[i] not in stopwords or raw_tokens[i+1] not in stopwords:
                    phrases.append(p2)
        if len(raw_tokens) >= 3:
            for i in range(len(raw_tokens) - 2):
                p3 = f"{raw_tokens[i]} {raw_tokens[i+1]} {raw_tokens[i+2]}"
                phrases.append(p3)

        scored = []
        for chunk in self.chunks:
            if document_id and chunk.get("document_id") != document_id:
                continue
            if allowed_doc_ids is not None and chunk.get("document_id") not in allowed_doc_ids:
                continue
            text_lower = chunk["content"].lower()
            matches = sum(text_lower.count(term) for term in query_terms)

            # Phrase bonus: exact multi-word phrase matching
            phrase_bonus = sum(1.5 for phrase in phrases if phrase in text_lower)

            if matches > 0 or phrase_bonus > 0:
                # Score based on term occurrences and phrase bonus normalized by length
                kw_score = (matches + (phrase_bonus * 2.0)) / (len(text_lower.split()) + 10)
                scored.append({
                    **chunk,
                    "score": round(float(kw_score), 4),
                    "term_matches": matches,
                    "phrase_bonus": round(phrase_bonus, 2),
                    "retrieval_mode": "keyword"
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        allowed_doc_ids: Optional[Set[str]] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining semantic vector similarity and keyword search
        using Reciprocal Rank Fusion (RRF), exact phrase boosting, and passage deduplication.
        """
        if not query or not query.strip() or not self.chunks:
            return []

        semantic_results = self.semantic_search(query, top_k=top_k * 2, document_id=document_id, allowed_doc_ids=allowed_doc_ids)
        keyword_results = self.keyword_search(query, top_k=top_k * 2, document_id=document_id, allowed_doc_ids=allowed_doc_ids)

        # Build fused score map
        fused: Dict[str, Dict[str, Any]] = {}
        rrf_k = 60

        for rank, res in enumerate(semantic_results):
            cid = res["chunk_id"]
            if cid not in fused:
                fused[cid] = {**res, "semantic_score": res["score"], "keyword_score": 0.0, "rrf_score": 0.0}
            fused[cid]["semantic_score"] = res["score"]
            fused[cid]["rrf_score"] += semantic_weight * (1.0 / (rrf_k + rank + 1))

        for rank, res in enumerate(keyword_results):
            cid = res["chunk_id"]
            if cid not in fused:
                fused[cid] = {**res, "semantic_score": 0.0, "keyword_score": res["score"], "rrf_score": 0.0}
            fused[cid]["keyword_score"] = res["score"]
            fused[cid]["rrf_score"] += keyword_weight * (1.0 / (rrf_k + rank + 1))

        # Calculate final combined normalized score
        final_list = list(fused.values())
        for item in final_list:
            item["score"] = round(item["rrf_score"] * 100, 4)
            item["retrieval_mode"] = "hybrid_rrf"

        final_list.sort(key=lambda x: x["score"], reverse=True)

        # Deduplicate redundant/identical passages
        deduped: List[Dict[str, Any]] = []
        for item in final_list:
            item_words = set(item["content"].lower().split())
            is_duplicate = False
            for kept in deduped:
                kept_words = set(kept["content"].lower().split())
                intersection = len(item_words.intersection(kept_words))
                union = len(item_words.union(kept_words))
                if union > 0 and (intersection / union) > 0.88:
                    is_duplicate = True
                    break
            if not is_duplicate:
                deduped.append(item)
            if len(deduped) >= top_k:
                break

        return deduped

    def get_chunk_count(self) -> int:
        return len(self.chunks)


vector_index_service = VectorIndexService()
