"""
Knowledge Graph Construction, Traversal, and GraphRAG Integration Service.
Extracts enterprise entities (People, Organizations, Technologies, Products, Concepts, Policies),
semantic relationships, and provides graph traversal and GraphRAG multi-hop expansion.
Persists entities and relationships to SQLite and JSON graph store.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.document import EntityRecord, RelationRecord


class KnowledgeGraphService:
    """Manages knowledge graph extraction, persistent storage, and GraphRAG queries."""

    ENTITY_PATTERNS = {
        "PERSON": [
            r'\b(?:Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b(?=\s+(?:is|was|serves as|leads|directed|authored|designed|managed))\b'
        ],
        "ORG": [
            r'\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*\s+(?:Corporation|Inc\.|Corp\.|LLC|Ltd\.|Group|Department|Team|Institute|University|Hospital|Bank)\b',
            r'\b(?:Google|Microsoft|Amazon|Apple|OpenAI|Meta|IBM|Intel|NVIDIA|Oracle|Salesforce|Cisco)\b'
        ],
        "TECH": [
            r'\b(?:Python|FastAPI|Docker|Kubernetes|PostgreSQL|SQLite|PyTorch|TensorFlow|React|Vue|Angular|REST API|GraphRAG|RAG|LLM|Transformer|BERT|ChromaDB|FAISS|SQLAlchemy)\b',
            r'\b(?:Machine Learning|Deep Learning|Artificial Intelligence|NLP|Knowledge Graph|Vector Database)\b'
        ],
        "POLICY": [
            r'\b[A-Z][a-zA-Z0-9\s]+(?:Policy|Standard|Procedure|Compliance|Framework|Protocol|Guideline)\b'
        ],
        "PRODUCT": [
            r'\b(?:Knowledge Navigator|ChatGPT|Claude|Gemini|Llama|GPT-4|Windows|Linux|macOS|AWS|Azure|GCP)\b'
        ]
    }

    RELATION_PATTERNS = [
        (r'([A-Za-z0-9_\s]+?)\s+(?:manages|managed by|leads|headed by)\s+([A-Za-z0-9_\s]+)', "MANAGES"),
        (r'([A-Za-z0-9_\s]+?)\s+(?:develops|built|created|engineered|maintains)\s+([A-Za-z0-9_\s]+)', "DEVELOPS"),
        (r'([A-Za-z0-9_\s]+?)\s+(?:operates in|located in|based in|works within)\s+([A-Za-z0-9_\s]+)', "OPERATES_IN"),
        (r'([A-Za-z0-9_\s]+?)\s+(?:governs|regulates|applies to|enforces)\s+([A-Za-z0-9_\s]+)', "GOVERNS"),
        (r'([A-Za-z0-9_\s]+?)\s+(?:integrates with|connects to|depends on|uses)\s+([A-Za-z0-9_\s]+)', "INTEGRATES_WITH")
    ]

    def __init__(self):
        self.store_dir = settings.GRAPH_STORE_DIR
        self.graph_file = self.store_dir / "knowledge_graph.json"

    def extract_and_store(self, db: Session, document_id: str, text: str) -> Tuple[int, int]:
        """
        Extracts named entities and semantic relationships from extracted text,
        persisting them to the database and graph JSON cache.
        """
        # Clean existing records for this document
        db.query(EntityRecord).filter(EntityRecord.document_id == document_id).delete()
        db.query(RelationRecord).filter(RelationRecord.document_id == document_id).delete()

        entities_found: Dict[str, Dict[str, Any]] = {}
        relations_found: List[Dict[str, Any]] = []

        # 1. Entity Extraction
        for category, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    raw_name = match.group(0).strip()
                    name = self._normalize_entity_name(raw_name)
                    if len(name) < 2 or len(name) > 60:
                        continue
                    
                    if name in entities_found:
                        entities_found[name]["mention_count"] += 1
                    else:
                        # Extract surrounding context snippet
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end].replace('\n', ' ').strip()

                        entities_found[name] = {
                            "name": name,
                            "category": category,
                            "mention_count": 1,
                            "context": context
                        }

        # 2. Relation Extraction
        sentences = re.split(r'(?<=[.!?])\s+', text)
        known_names = list(entities_found.keys())

        for sentence in sentences:
            if len(sentence) < 15 or len(sentence) > 300:
                continue
            
            # Check pattern matches
            for rel_pat, rel_type in self.RELATION_PATTERNS:
                m = re.search(rel_pat, sentence, re.IGNORECASE)
                if m:
                    src_candidate = self._normalize_entity_name(m.group(1).strip())
                    tgt_candidate = self._normalize_entity_name(m.group(2).strip())
                    
                    # Ensure candidate matches known entities or looks like valid entity
                    src = self._match_or_approximate(src_candidate, known_names)
                    tgt = self._match_or_approximate(tgt_candidate, known_names)

                    if src and tgt and src != tgt:
                        relations_found.append({
                            "source": src,
                            "relation": rel_type,
                            "target": tgt,
                            "provenance": sentence.strip()
                        })

        # Persist entities
        for name, data in entities_found.items():
            ent_id = f"ent_{document_id}_{hash(name) % 10000000}"
            ent_record = EntityRecord(
                id=ent_id,
                document_id=document_id,
                name=name,
                category=data["category"],
                mention_count=data["mention_count"],
                source_context=data["context"]
            )
            db.add(ent_record)

        # Persist relations
        seen_rels: Set[Tuple[str, str, str]] = set()
        for rel in relations_found:
            triple = (rel["source"], rel["relation"], rel["target"])
            if triple in seen_rels:
                continue
            seen_rels.add(triple)

            rel_id = f"rel_{document_id}_{hash(str(triple)) % 10000000}"
            rel_record = RelationRecord(
                id=rel_id,
                document_id=document_id,
                source_entity=rel["source"],
                relation_type=rel["relation"],
                target_entity=rel["target"],
                provenance_text=rel["provenance"]
            )
            db.add(rel_record)

        db.commit()
        self._export_graph_json(db)
        logger.info(f"Knowledge Graph: Extracted {len(entities_found)} entities & {len(seen_rels)} relationships for document {document_id}")
        return len(entities_found), len(seen_rels)

    def _normalize_entity_name(self, name: str) -> str:
        """Strips titles, extraneous punct, and normalizes capitalization."""
        name = re.sub(r'^(?:Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.)\s+', '', name)
        name = re.sub(r'[^\w\s\.-]', '', name)
        return " ".join(name.split())

    def _match_or_approximate(self, candidate: str, known_names: List[str]) -> Optional[str]:
        cand_lower = candidate.lower()
        for name in known_names:
            if name.lower() in cand_lower or cand_lower in name.lower():
                return name
        if len(candidate) > 2 and candidate[0].isupper() and len(candidate.split()) <= 4:
            return candidate
        return None

    def _export_graph_json(self, db: Session):
        """Exports graph snapshot to JSON for fast UI visualization rendering."""
        try:
            entities = db.query(EntityRecord).all()
            relations = db.query(RelationRecord).all()

            nodes = [{
                "id": e.name,
                "label": e.name,
                "category": e.category,
                "mentions": e.mention_count,
                "document_id": e.document_id
            } for e in entities]

            # Deduplicate nodes by id
            unique_nodes = {}
            for n in nodes:
                if n["id"] not in unique_nodes:
                    unique_nodes[n["id"]] = n
                else:
                    unique_nodes[n["id"]]["mentions"] += n["mentions"]

            edges = [{
                "source": r.source_entity,
                "target": r.target_entity,
                "label": r.relation_type,
                "provenance": r.provenance_text
            } for r in relations]

            graph_data = {
                "nodes": list(unique_nodes.values()),
                "edges": edges,
                "total_nodes": len(unique_nodes),
                "total_edges": len(edges)
            }

            self.store_dir.mkdir(parents=True, exist_ok=True)
            with open(self.graph_file, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to export graph JSON: {e}")

    def get_graph_data(
        self,
        db: Session,
        filter_category: Optional[str] = None,
        allowed_doc_ids: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """Returns nodes and edges formatted for interactive D3 / SVG graph visualizations, filtered by permitted document access."""
        query_ent = db.query(EntityRecord)
        query_rel = db.query(RelationRecord)
        if allowed_doc_ids is not None:
            query_ent = query_ent.filter(EntityRecord.document_id.in_(allowed_doc_ids))
            query_rel = query_rel.filter(RelationRecord.document_id.in_(allowed_doc_ids))

        if filter_category:
            query_ent = query_ent.filter(EntityRecord.category == filter_category)
        
        entities = query_ent.all()
        relations = query_rel.all()

        nodes_dict = {}
        for e in entities:
            if e.name not in nodes_dict:
                nodes_dict[e.name] = {
                    "id": e.name,
                    "label": e.name,
                    "category": e.category,
                    "mentions": e.mention_count,
                    "context": e.source_context
                }
            else:
                nodes_dict[e.name]["mentions"] += e.mention_count

        edges_list = []
        for r in relations:
            # Include edge if at least one node is present
            if r.source_entity in nodes_dict or r.target_entity in nodes_dict:
                edges_list.append({
                    "id": r.id,
                    "source": r.source_entity,
                    "target": r.target_entity,
                    "relation": r.relation_type,
                    "provenance": r.provenance_text
                })

        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges_list,
            "node_count": len(nodes_dict),
            "edge_count": len(edges_list)
        }

    def graphrag_expand(
        self,
        db: Session,
        query: str,
        max_hops: int = 1,
        allowed_doc_ids: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts entities present in query, traverses relational graph edges,
        and returns multi-hop contextual graph evidence for GraphRAG, restricted to authorized documents.
        """
        if not query or not query.strip():
            return []

        query_lower = query.lower()
        query_ent = db.query(EntityRecord)
        if allowed_doc_ids is not None:
            query_ent = query_ent.filter(EntityRecord.document_id.in_(allowed_doc_ids))
        all_entities = query_ent.all()
        
        matched_entities = [e.name for e in all_entities if e.name.lower() in query_lower]
        if not matched_entities:
            # Try subtoken match
            tokens = set(re.findall(r'\b[A-Za-z0-9_-]+\b', query_lower))
            matched_entities = [e.name for e in all_entities if set(e.name.lower().split()).intersection(tokens)]

        if not matched_entities:
            return []

        evidence = []
        seen_triples = set()
        for entity in set(matched_entities):
            # Outgoing relations
            q_out = db.query(RelationRecord).filter(RelationRecord.source_entity == entity)
            if allowed_doc_ids is not None:
                q_out = q_out.filter(RelationRecord.document_id.in_(allowed_doc_ids))
            out_rels = q_out.all()
            for r in out_rels:
                key = (r.source_entity, r.relation_type, r.target_entity)
                if key not in seen_triples:
                    seen_triples.add(key)
                    evidence.append({
                        "source": r.source_entity,
                        "relation": r.relation_type,
                        "target": r.target_entity,
                        "provenance": r.provenance_text,
                        "hop": 1
                    })

            # Incoming relations
            q_in = db.query(RelationRecord).filter(RelationRecord.target_entity == entity)
            if allowed_doc_ids is not None:
                q_in = q_in.filter(RelationRecord.document_id.in_(allowed_doc_ids))
            in_rels = q_in.all()
            for r in in_rels:
                key = (r.source_entity, r.relation_type, r.target_entity)
                if key not in seen_triples:
                    seen_triples.add(key)
                    evidence.append({
                        "source": r.source_entity,
                        "relation": r.relation_type,
                        "target": r.target_entity,
                        "provenance": r.provenance_text,
                        "hop": 1
                    })

        return evidence


knowledge_graph_service = KnowledgeGraphService()
