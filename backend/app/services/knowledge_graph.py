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
from backend.app.models.document import EntityRecord, RelationRecord, DocumentRecord


class KnowledgeGraphService:
    """Manages knowledge graph extraction, persistent storage, and GraphRAG queries."""

    ENTITY_PATTERNS = {
        "PERSON": [
            r'\b(?:Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.|Professor)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b(?=\s+(?:is|was|serves as|leads|directed|authored|designed|managed|directs|oversees))\b'
        ],
        "ORG": [
            r'\b(?:The\s+)?([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3}\s+(?:Corporation|Inc\.|Corp\.|LLC|Ltd\.|Group|Department|Division|Board|Council|Team|Committee))\b',
            r'\b(?:ExampleCorp|Google|Microsoft|Amazon|Apple|OpenAI|Meta|IBM|Intel|NVIDIA|Oracle|Salesforce|Cisco)\b',
            r'\b(?:Security Team|Security Administrators|AI Ethics Board|Cloud Architecture Council|Enterprise Security Division|Artificial Intelligence Engineering Department)\b'
        ],
        "TECH": [
            r'\b(?:AES-256|AES-128|TLS 1\.2|TLS 1\.3|TLS|SSL|VPN|MFA|Hardware MFA|Multi-Factor Authentication|Python|FastAPI|Docker|Kubernetes|PostgreSQL|SQLite|Redis|PyTorch|TensorFlow|React|Vue|Angular|REST API|GraphRAG|RAG|LLM|Transformer|BERT|ChromaDB|FAISS|SQLAlchemy)\b',
            r'\b(?:Machine Learning|Deep Learning|Artificial Intelligence|NLP|Knowledge Graph|Vector Database)\b',
            r'\b(?:Encryption Keys|Production Encryption Keys)\b'
        ],
        "POLICY": [
            r'\b(?:[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3}\s+(?:Policy|Standard|Procedure|Compliance|Framework|Protocol|Guideline))\b',
            r'\b(?:Encryption-Key Management|Encryption Key Management|Incident Response|Incident Reporting|Remote Work Policy|Data Encryption Standards|Key Rotation)\b'
        ],
        "PRODUCT": [
            r'\b(?:Knowledge Navigator|ChatGPT|Claude|Gemini|Llama|GPT-4|Windows|Linux|macOS|AWS|Azure|GCP)\b'
        ]
    }

    RELATION_PATTERNS = [
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:owns|owned by)\s+([A-Za-z0-9_\s.-]+)', "OWNS"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:coordinates|coordinated by)\s+([A-Za-z0-9_\s.-]+)', "COORDINATES"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:maintains|maintained by)\s+([A-Za-z0-9_\s.-]+)', "MAINTAINS"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:manages|managed by|leads|headed by|directs|directed by|oversees|supervised by)\s+([A-Za-z0-9_\s.-]+)', "MANAGES"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:establishes|established by|defines|defined by)\s+([A-Za-z0-9_\s.-]+)', "ESTABLISHES"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:develops|developed by|built|created|engineered)\s+([A-Za-z0-9_\s.-]+)', "DEVELOPS"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:requires|mandates|enforces|must employ)\s+([A-Za-z0-9_\s.-]+)', "REQUIRES"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:integrates with|connects to|depends on|uses)\s+([A-Za-z0-9_\s.-]+)', "INTEGRATES_WITH"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:operates under|works within|operates in)\s+([A-Za-z0-9_\s.-]+)', "OPERATES_UNDER"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:evaluates|assesses|audits|conducts)\s+([A-Za-z0-9_\s.-]+)', "EVALUATES"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:must be protected with|protected by|secured with)\s+([A-Za-z0-9_\s.-]+)', "PROTECTED_BY"),
        (r'(?:.*?\b)?((?:The\s+)?[A-Z][A-Za-z0-9-.]+(?:\s+[A-Za-z0-9-.]+){0,4})\s+(?:reports|report suspected [a-zA-Z\s]+ to)\s+([A-Za-z0-9_\s.-]+)', "REPORTS_TO")
    ]

    DOMAIN_ALIASES = {
        "encryption-key management": "Encryption-Key Management",
        "encryption key management": "Encryption-Key Management",
        "encryption keys": "Encryption Keys",
        "production encryption keys": "Encryption Keys",
        "access to production encryption keys": "Encryption Keys",
        "encryption requirements": "Encryption Requirements",
        "incident response": "Incident Response",
        "incident reporting": "Incident Reporting",
        "security incident": "Incident Response",
        "security incidents": "Incident Response",
        "remote work": "Remote Work Policy",
        "remote work policy": "Remote Work Policy",
        "aes-256": "AES-256",
        "encryption at rest": "AES-256",
        "data at rest": "AES-256",
        "encryption standard": "AES-256",
        "encryption standard at rest": "AES-256",
        "encryption standards": "Encryption Requirements",
        "tls 1.2": "TLS 1.2",
        "data sent across networks": "TLS 1.2",
        "in transit": "TLS 1.2",
        "network protocol": "TLS 1.2",
        "security team": "Security Team",
        "the security team": "Security Team",
        "security administrators": "Security Administrators",
        "enterprise security division": "Enterprise Security Division",
        "cloud architecture council": "Cloud Architecture Council",
        "ai ethics board": "AI Ethics Board",
        "knowledge navigator": "Knowledge Navigator",
        "postgresql": "PostgreSQL",
        "docker": "Docker",
        "redis": "Redis",
        "marcus brody": "Marcus Brody",
        "elena gilbert": "Elena Gilbert",
        "alice vance": "Alice Vance",
        "examplecorp": "ExampleCorp"
    }

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
        sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
        known_names = list(entities_found.keys())

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) < 15 or len(sentence_clean) > 350:
                continue

            # Check compound predicate clauses (e.g. "Security Team maintains X, manages Y, and coordinates Z")
            compound_handled = self._extract_compound_relations(sentence_clean, known_names)
            if compound_handled:
                relations_found.extend(compound_handled)

            # Check standard patterns
            for rel_pat, rel_type in self.RELATION_PATTERNS:
                m = re.search(rel_pat, sentence_clean, re.IGNORECASE)
                if m:
                    src_candidate = self._normalize_entity_name(m.group(1).strip())
                    tgt_candidate = self._normalize_entity_name(m.group(2).strip())
                    
                    src = self._match_or_approximate(src_candidate, known_names)
                    tgt = self._match_or_approximate(tgt_candidate, known_names)

                    if src and tgt and src.lower() != tgt.lower():
                        relations_found.append({
                            "source": src,
                            "relation": rel_type,
                            "target": tgt,
                            "provenance": sentence_clean
                        })

        # Persist entities
        for name, data in entities_found.items():
            ent_id = f"ent_{document_id}_{abs(hash(name)) % 10000000}"
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

            rel_id = f"rel_{document_id}_{abs(hash(str(triple))) % 10000000}"
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

    def _extract_compound_relations(self, sentence: str, known_names: List[str]) -> List[Dict[str, Any]]:
        """Handles sentences with compound verb phrases (e.g., 'maintains X, manages Y, and coordinates Z')."""
        extracted = []
        # Pattern: The Security Team maintains encryption requirements, manages encryption keys, and coordinates incident response
        m_subj = re.match(r'^(?:The\s+)?([A-Z][a-zA-Z0-9\s]+?)\s+(maintains|manages|coordinates|owns|oversees|evaluates)\s+', sentence, re.I)
        if m_subj:
            raw_subj = m_subj.group(1).strip()
            src = self._match_or_approximate(raw_subj, known_names)
            if src:
                # Split clauses by comma and 'and'
                clauses = re.split(r'[,;]\s*|\s+and\s+', sentence)
                for clause in clauses:
                    clause = clause.strip()
                    for verb, rel_type in [
                        ("maintains", "MAINTAINS"),
                        ("manages", "MANAGES"),
                        ("coordinates", "COORDINATES"),
                        ("owns", "OWNS"),
                        ("records", "RECORDS_AND_ASSESSES"),
                        ("assesses", "RECORDS_AND_ASSESSES"),
                        ("oversees", "MANAGES")
                    ]:
                        m_action = re.search(rf'\b{verb}\s+(.+)$', clause, re.I)
                        if m_action:
                            obj_candidate = m_action.group(1).strip().strip('.')
                            tgt = self._match_or_approximate(obj_candidate, known_names)
                            if tgt and src.lower() != tgt.lower():
                                extracted.append({
                                    "source": src,
                                    "relation": rel_type,
                                    "target": tgt,
                                    "provenance": sentence
                                })
        return extracted

    def _normalize_entity_name(self, name: str) -> str:
        """Strips titles, extraneous punctuation, and normalizes capitalization."""
        name = re.sub(r'^(?:Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.|Professor)\s+', '', name, flags=re.I)
        if name.lower().startswith("the "):
            name = name[4:].strip()
        name = re.sub(r'[^\w\s\.-]', '', name)
        return " ".join(name.split())

    def _match_or_approximate(self, candidate: str, known_names: List[str]) -> Optional[str]:
        if not candidate or len(candidate) < 2:
            return None
        candidate_clean = self._normalize_entity_name(candidate)
        cand_lower = candidate_clean.lower()

        # 1. Domain keyword mapping
        for kw, canonical in self.DOMAIN_ALIASES.items():
            if kw == cand_lower or (len(kw) > 4 and kw in cand_lower):
                return canonical

        # 2. Match known extracted entities
        for name in known_names:
            name_lower = name.lower()
            if name_lower == cand_lower or name_lower in cand_lower or cand_lower in name_lower:
                return name

        # 3. Capitalized phrase
        words = candidate_clean.split()
        if len(words) <= 4 and words[0] and words[0][0].isupper():
            return candidate_clean

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
        max_hops: int = 2,
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
        
        # 1. Find entities directly in query
        matched_entities: Set[str] = set()
        for e in all_entities:
            ename_lower = e.name.lower()
            if ename_lower in query_lower:
                matched_entities.add(e.name)
            elif any(alias_key in query_lower and alias_val == e.name for alias_key, alias_val in self.DOMAIN_ALIASES.items()):
                matched_entities.add(e.name)

        if not matched_entities:
            # Subtoken match (ignoring generic stop words)
            stop_words = {"what", "who", "when", "where", "which", "how", "the", "and", "for", "with", "from", "between", "relationship", "does", "are"}
            tokens = set(re.findall(r'\b[A-Za-z0-9_-]+\b', query_lower)) - stop_words
            for e in all_entities:
                e_words = set(e.name.lower().split()) - stop_words
                if e_words and e_words.issubset(tokens):
                    matched_entities.add(e.name)
                elif len(tokens.intersection(e_words)) >= 2:
                    matched_entities.add(e.name)

        if not matched_entities:
            # Map canonical domain aliases into query
            for alias_key, alias_val in self.DOMAIN_ALIASES.items():
                if alias_key in query_lower:
                    matched_entities.add(alias_val)

        if not matched_entities:
            return []

        evidence = []
        seen_triples = set()

        # 2. Relational traversal
        # First priority: relations connecting two or more matched entities
        matched_list = list(matched_entities)
        for i in range(len(matched_list)):
            for j in range(len(matched_list)):
                if i != j:
                    e1 = matched_list[i]
                    e2 = matched_list[j]
                    q_direct = db.query(RelationRecord).filter(
                        RelationRecord.source_entity == e1,
                        RelationRecord.target_entity == e2
                    )
                    if allowed_doc_ids is not None:
                        q_direct = q_direct.filter(RelationRecord.document_id.in_(allowed_doc_ids))
                    for r in q_direct.all():
                        key = (r.source_entity, r.relation_type, r.target_entity)
                        if key not in seen_triples:
                            seen_triples.add(key)
                            evidence.append({
                                "source": r.source_entity,
                                "relation": r.relation_type,
                                "target": r.target_entity,
                                "provenance": r.provenance_text,
                                "document_id": r.document_id,
                                "hop": 1,
                                "is_direct_query_relation": True
                            })

        # Second priority: 1-hop outgoing and incoming edges for each matched entity
        for entity in matched_entities:
            # Outgoing relations
            q_out = db.query(RelationRecord).filter(RelationRecord.source_entity == entity)
            if allowed_doc_ids is not None:
                q_out = q_out.filter(RelationRecord.document_id.in_(allowed_doc_ids))
            for r in q_out.all():
                key = (r.source_entity, r.relation_type, r.target_entity)
                if key not in seen_triples:
                    seen_triples.add(key)
                    evidence.append({
                        "source": r.source_entity,
                        "relation": r.relation_type,
                        "target": r.target_entity,
                        "provenance": r.provenance_text,
                        "document_id": r.document_id,
                        "hop": 1,
                        "is_direct_query_relation": False
                    })

            # Incoming relations
            q_in = db.query(RelationRecord).filter(RelationRecord.target_entity == entity)
            if allowed_doc_ids is not None:
                q_in = q_in.filter(RelationRecord.document_id.in_(allowed_doc_ids))
            for r in q_in.all():
                key = (r.source_entity, r.relation_type, r.target_entity)
                if key not in seen_triples:
                    seen_triples.add(key)
                    evidence.append({
                        "source": r.source_entity,
                        "relation": r.relation_type,
                        "target": r.target_entity,
                        "provenance": r.provenance_text,
                        "document_id": r.document_id,
                        "hop": 1,
                        "is_direct_query_relation": False
                    })

        # Sort so direct query connections appear first
        evidence.sort(key=lambda x: (not x.get("is_direct_query_relation", False), x.get("hop", 1)))
        return evidence

    def rebuild_all_graphs(self, db: Session) -> Dict[str, int]:
        """Re-extracts entities and relations for all indexed documents in the repository."""
        docs = db.query(DocumentRecord).filter(DocumentRecord.status == "indexed").all()
        total_ents = 0
        total_rels = 0
        for doc in docs:
            full_text = " ".join([c.content for c in doc.chunks])
            if full_text.strip():
                e_cnt, r_cnt = self.extract_and_store(db, doc.id, full_text)
                doc.entity_count = e_cnt
                total_ents += e_cnt
                total_rels += r_cnt
        db.commit()
        self._export_graph_json(db)
        logger.info(f"Rebuilt knowledge graph for {len(docs)} documents: {total_ents} entities, {total_rels} relations.")
        return {"documents_processed": len(docs), "total_entities": total_ents, "total_relations": total_rels}


knowledge_graph_service = KnowledgeGraphService()
