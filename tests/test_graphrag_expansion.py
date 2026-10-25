"""
Automated Verification Tests for Grounded AI Answers, Formatting,
Source Citations, GraphRAG Toggle, and Evidence Validation.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)


def test_graphrag_relational_toggle_behavior():
    """
    Verifies that toggling 'enable_graphrag' between True and False produces
    distinct retrieval modes and properly separates graph relations from the main answer.
    """
    rel_question = "What is the relationship between the Security Team, encryption-key management, and incident response?"

    # 1. Ask with GraphRAG ENABLED
    res_enabled = client.post(
        f"{settings.API_V1_STR}/navigator/ask",
        json={"question": rel_question, "enable_graphrag": True, "top_k": 4}
    )
    assert res_enabled.status_code == 200
    data_enabled = res_enabled.json()

    assert data_enabled["retrieval_mode"] == "GraphRAG"
    assert len(data_enabled["graph_evidence"]) > 0
    assert data_enabled["synthesis_engine"] == "graphrag_extractive_verified"
    assert data_enabled["is_grounded"] is True
    assert data_enabled["claim_support_rate"] >= 0.8
    assert len(data_enabled["sources"]) >= 1

    ans_enabled = data_enabled["answer"]
    assert "**Answer**" in ans_enabled
    assert "**Source**" in ans_enabled or "**Sources**" in ans_enabled
    assert "Security Team" in ans_enabled
    assert "encryption-key management" in ans_enabled.lower()
    assert "incident response" in ans_enabled.lower()
    # Technical graph triples belong in graph_evidence, not dumped as raw debug text in the answer
    assert "--[" not in ans_enabled
    assert any(g["relation"] in ("OWNS", "COORDINATES", "MANAGES", "MAINTAINS") for g in data_enabled["graph_evidence"])

    # 2. Ask with GraphRAG DISABLED
    res_disabled = client.post(
        f"{settings.API_V1_STR}/navigator/ask",
        json={"question": rel_question, "enable_graphrag": False, "top_k": 4}
    )
    assert res_disabled.status_code == 200
    data_disabled = res_disabled.json()

    assert data_disabled["retrieval_mode"] == "Hybrid RAG"
    assert len(data_disabled["graph_evidence"]) == 0
    assert data_disabled["synthesis_engine"] == "extractive_verified"
    assert data_disabled["is_grounded"] is True
    assert len(data_disabled["sources"]) >= 1

    ans_disabled = data_disabled["answer"]
    assert "**Answer**" in ans_disabled
    assert "--[" not in ans_disabled


def test_nine_benchmark_questions():
    """
    Comprehensive verification of the 9 specific user benchmark questions.
    Checks answer correctness, relevance, formatting, source attribution, and abstention.
    """
    # Q1: Encryption standard at rest
    r1 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "What encryption standard must be used for enterprise data at rest?", "enable_graphrag": True}).json()
    assert "AES-256" in r1["answer"]
    assert "Demo_Enterprise_Security_Policy.docx" in r1["answer"]
    assert "Data Encryption" in r1["answer"]
    assert "TLS" not in r1["answer"]
    assert "VPN" not in r1["answer"]

    # Q2: Protocol protecting data across networks
    r2 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "Which protocol protects data sent across networks?", "enable_graphrag": True}).json()
    assert "TLS 1.2" in r2["answer"]
    assert "Demo_Enterprise_Security_Policy.docx" in r2["answer"]
    assert "AES-256" not in r2["answer"]

    # Q3: Encryption key rotation frequency
    r3 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "How often must production encryption keys be rotated?", "enable_graphrag": True}).json()
    assert "90 days" in r3["answer"]
    assert "Demo_Enterprise_Security_Policy.docx" in r3["answer"]
    assert "Encryption Key Management" in r3["answer"]

    # Q4: Responsibility for encryption-key management
    r4 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "Who is responsible for encryption-key management?", "enable_graphrag": True}).json()
    assert "Security Team" in r4["answer"]
    assert "Demo_Enterprise_Security_Policy.docx" in r4["answer"]
    assert "Encryption Key Management" in r4["answer"]

    # Q5: Remote access requirements
    r5 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "What must employees use to access company resources remotely?", "enable_graphrag": True}).json()
    assert "company VPN" in r5["answer"] or "VPN" in r5["answer"]
    assert "MFA" in r5["answer"] or "Multi-factor authentication" in r5["answer"]
    assert "Demo_Enterprise_Security_Policy.docx" in r5["answer"]
    assert "Remote Work" in r5["answer"]

    # Q6: Security incident reporting deadline
    r6 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "How soon must a suspected security incident be reported?", "enable_graphrag": True}).json()
    assert "24 hours" in r6["answer"]
    assert "Demo_Enterprise_Security_Policy.docx" in r6["answer"]
    assert "Security Incident Reporting" in r6["answer"]

    # Q7: Security Team relationship
    r7 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "What is the relationship between the Security Team, encryption-key management, and incident response?", "enable_graphrag": True}).json()
    assert "Security Team" in r7["answer"]
    assert "encryption-key management" in r7["answer"].lower()
    assert "incident response" in r7["answer"].lower()
    assert "Demo_Enterprise_Security_Policy.docx" in r7["answer"]

    # Q8: Conflict detection on encryption standard
    r8 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "What encryption standard is required? If the documents contain conflicting requirements, identify the conflict and cite both sources rather than silently choosing one.", "enable_graphrag": True}).json()
    assert "AES-256" in r8["answer"]
    assert "Demo_Enterprise_Security_Policy.docx" in r8["answer"]
    assert "test_governance_manual.docx" in r8["answer"]
    assert len(r8["sources"]) >= 2

    # Q9: Unsupported policy (Maternity leave)
    r9 = client.post(f"{settings.API_V1_STR}/navigator/ask", json={"question": "What is the company's maternity leave policy? If no supporting document contains this information, state that it was not found in the available documents.", "enable_graphrag": True}).json()
    assert r9["verification_status"] == "abstained"
    assert r9["confidence"] == 0.0
    assert r9["is_grounded"] is False
    assert len(r9["sources"]) == 0
    assert "could not find information" in r9["answer"].lower() or "not found" in r9["answer"].lower()


def test_clean_formatting_and_no_raw_markdown_leak():
    """
    Verifies that the generated answer does not contain document headers,
    suggested question titles, or markdown table delimiters.
    """
    res = client.post(
        f"{settings.API_V1_STR}/navigator/ask",
        json={"question": "What encryption standard must be used for enterprise data at rest?", "enable_graphrag": True}
    )
    assert res.status_code == 200
    data = res.json()

    ans = data["answer"]
    assert "Suggested Questions for the Knowledge Navigator" not in ans
    assert "9. Suggested Questions" not in ans
    assert "| Requirement" not in ans
    assert "DEMO ENTERPRISE SECURITY POLICY" not in ans
    assert "**Answer**" in ans
    assert "**Source**" in ans


def test_citation_integrity_and_accuracy():
    """
    Verifies that returned sources have verified status and match the document metadata.
    """
    res = client.post(
        f"{settings.API_V1_STR}/navigator/ask",
        json={"question": "How often must production encryption keys be rotated?", "enable_graphrag": True}
    )
    assert res.status_code == 200
    data = res.json()

    assert len(data["sources"]) == 1
    src = data["sources"][0]
    assert src["verified"] is True
    assert src["filename"] == "Demo_Enterprise_Security_Policy.docx"
    assert src["page_number"] == 1
    assert "90 days" in src["snippet"]
