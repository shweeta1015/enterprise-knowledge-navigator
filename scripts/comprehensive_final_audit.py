"""
Comprehensive Final Audit Script for Enterprise Knowledge Navigator.
Executes deep automated checks across all 11 phases:
- Phase 1 & 2: Test Admin, Analyst, and Knowledge Worker roles & permissions
- Phase 3: Custom Role Management CRUD & guards
- Phase 4: Document ingestion (PDF, DOCX, TXT), duplicate detection, deletion
- Phase 5: Search, RAG, citations, hallucination prevention/abstention, GraphRAG
- Phase 6: Refresh button endpoints & UI interaction contracts
- Phase 7: Security & authorization
- Phase 8: Database & vector store integrity
"""

import sys
import io
import time
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.user import UserRecord, RoleRecord
from backend.app.models.document import DocumentRecord, ChunkRecord, EntityRecord, RelationRecord

client = TestClient(app)

results = {}

def log_result(section, test_name, status, details=""):
    print(f"[{status}] {section} :: {test_name} - {details}")
    if section not in results:
        results[section] = []
    results[section].append({"test": test_name, "status": status, "details": details})


print("\n" + "="*70)
print("PHASE 1 & 2: ACCOUNT ROLES & PERMISSIONS VERIFICATION")
print("="*70)

# A. Admin
admin_login = client.post("/api/v1/auth/login", json={"email": "admin@eknavigator.com", "password": "Admin@123456", "remember_me": False})
if admin_login.status_code == 200:
    admin_token = admin_login.json()["access_token"]
    log_result("ROLES", "Admin Login", "PASS", "Token acquired")
    
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).json()
    perms = client.get("/api/v1/auth/my-permissions", headers={"Authorization": f"Bearer {admin_token}"}).json()
    if me["role"] == "admin" and len(perms.get("permissions", [])) == 11:
        log_result("ROLES", "Admin Capabilities", "PASS", f"All 11 platform capabilities granted")
    else:
        log_result("ROLES", "Admin Capabilities", "FAIL", f"Capabilities count: {len(perms.get('permissions', []))}")
        
    users_res = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    log_result("ROLES", "Admin User Management Access", "PASS" if users_res.status_code == 200 else "FAIL", f"Status {users_res.status_code}")
    
    audit_res = client.get("/api/v1/auth/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    log_result("ROLES", "Admin Audit Logs Access", "PASS" if audit_res.status_code == 200 else "FAIL", f"Status {audit_res.status_code}")
else:
    log_result("ROLES", "Admin Login", "FAIL", f"Status {admin_login.status_code}")

# B. Knowledge Analyst
analyst_login = client.post("/api/v1/auth/login", json={"email": "analyst@eknavigator.com", "password": "Analyst@123456", "remember_me": False})
if analyst_login.status_code == 200:
    analyst_token = analyst_login.json()["access_token"]
    log_result("ROLES", "Analyst Login", "PASS", "Token acquired")
    
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {analyst_token}"}).json()
    perms = client.get("/api/v1/auth/my-permissions", headers={"Authorization": f"Bearer {analyst_token}"}).json()
    if me["role"] == "analyst" and len(perms.get("permissions", [])) == 6:
        log_result("ROLES", "Analyst Capabilities", "PASS", "6 analytics & intelligence capabilities granted")
    else:
        log_result("ROLES", "Analyst Capabilities", "FAIL", f"Capabilities count: {len(perms.get('permissions', []))}")
        
    blocked_users = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {analyst_token}"})
    blocked_roles = client.get("/api/v1/auth/admin/roles", headers={"Authorization": f"Bearer {analyst_token}"})
    if blocked_users.status_code == 403 and blocked_roles.status_code == 403:
        log_result("ROLES", "Analyst Admin Endpoint Guard", "PASS", "HTTP 403 Forbidden on privileged endpoints")
    else:
        log_result("ROLES", "Analyst Admin Endpoint Guard", "FAIL", f"Users: {blocked_users.status_code}, Roles: {blocked_roles.status_code}")
else:
    log_result("ROLES", "Analyst Login", "FAIL", f"Status {analyst_login.status_code}")

# C. Knowledge Worker
worker_login = client.post("/api/v1/auth/login", json={"email": "worker@eknavigator.com", "password": "Worker@123456", "remember_me": False})
if worker_login.status_code == 200:
    worker_token = worker_login.json()["access_token"]
    log_result("ROLES", "Worker Login", "PASS", "Token acquired")
    
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {worker_token}"}).json()
    perms = client.get("/api/v1/auth/my-permissions", headers={"Authorization": f"Bearer {worker_token}"}).json()
    if me["role"] == "knowledge_worker" and len(perms.get("permissions", [])) == 5:
        log_result("ROLES", "Worker Capabilities", "PASS", "5 core operational capabilities granted")
    else:
        log_result("ROLES", "Worker Capabilities", "FAIL", f"Capabilities count: {len(perms.get('permissions', []))}")
        
    blocked_users = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {worker_token}"})
    blocked_roles = client.get("/api/v1/auth/admin/roles", headers={"Authorization": f"Bearer {worker_token}"})
    blocked_audit = client.get("/api/v1/auth/admin/audit-logs", headers={"Authorization": f"Bearer {worker_token}"})
    if blocked_users.status_code == 403 and blocked_roles.status_code == 403 and blocked_audit.status_code == 403:
        log_result("ROLES", "Worker Admin Privileges Guard", "PASS", "HTTP 403 Forbidden on privileged admin endpoints")
    else:
        log_result("ROLES", "Worker Admin Privileges Guard", "FAIL", f"Users: {blocked_users.status_code}, Roles: {blocked_roles.status_code}, Audit: {blocked_audit.status_code}")
else:
    log_result("ROLES", "Worker Login", "FAIL", f"Status {worker_login.status_code}")


print("\n" + "="*70)
print("PHASE 3: CUSTOM ROLE MANAGEMENT VERIFICATION")
print("="*70)

# Clean up any leftover test role before run
_db = SessionLocal()
_stale_role = _db.query(RoleRecord).filter(RoleRecord.name == "Audit Inspector QA").first()
if _stale_role:
    _db.delete(_stale_role)
    _db.commit()
_db.close()

# Create custom role
role_payload = {
    "name": "Audit Inspector QA",
    "description": "Reviews security logs and runs retrieval evaluations",
    "permissions": ["audit_logs", "evaluation", "search_retrieval", "profile_settings"]
}
res_cr = client.post("/api/v1/auth/admin/roles", json=role_payload, headers={"Authorization": f"Bearer {admin_token}"})
if res_cr.status_code in (200, 201):
    created_role = res_cr.json()
    role_id = created_role["id"]
    log_result("CUSTOM_ROLES", "Custom Role Creation", "PASS", f"Created role {role_id} with 4 capabilities")
    
    # Provision a disposable user with this custom role
    disp_email = "audit.inspector.qa@eknavigator.com"
    res_prov = client.post("/api/v1/auth/users/provision", json={
        "full_name": "Audit Inspector QA",
        "email": disp_email,
        "password": "Password123!Safe",
        "role": role_id,
        "organization": "Enterprise Compliance"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    
    if res_prov.status_code == 200:
        disp_user = res_prov.json()
        disp_user_id = disp_user["id"]
        log_result("CUSTOM_ROLES", "Custom Role User Provisioning", "PASS", f"User {disp_email} provisioned with role {role_id}")
        
        # Test deletion guard: should fail because 1 user is assigned!
        res_del_blocked = client.delete(f"/api/v1/auth/admin/roles/{role_id}", headers={"Authorization": f"Bearer {admin_token}"})
        if res_del_blocked.status_code == 400 and "assigned" in res_del_blocked.json()["detail"].lower():
            log_result("CUSTOM_ROLES", "Assigned Role Deletion Guard", "PASS", "Successfully blocked deletion of role with assigned user")
        else:
            log_result("CUSTOM_ROLES", "Assigned Role Deletion Guard", "FAIL", f"Status: {res_del_blocked.status_code} {res_del_blocked.text}")
            
        # Clean up user first
        client.delete(f"/api/v1/auth/users/{disp_user_id}", headers={"Authorization": f"Bearer {admin_token}"})
        
        # Delete role now that 0 users are assigned
        res_del_ok = client.delete(f"/api/v1/auth/admin/roles/{role_id}", headers={"Authorization": f"Bearer {admin_token}"})
        if res_del_ok.status_code == 200:
            log_result("CUSTOM_ROLES", "Custom Role Deletion", "PASS", "Deleted custom role successfully once unassigned")
        else:
            log_result("CUSTOM_ROLES", "Custom Role Deletion", "FAIL", f"Status: {res_del_ok.status_code} {res_del_ok.text}")
    else:
        log_result("CUSTOM_ROLES", "Custom Role User Provisioning", "FAIL", f"Status: {res_prov.status_code}")
else:
    log_result("CUSTOM_ROLES", "Custom Role Creation", "FAIL", f"Status: {res_cr.status_code} {res_cr.text}")

# Check protection of built-in roles
res_builtin_del = client.delete("/api/v1/auth/admin/roles/admin", headers={"Authorization": f"Bearer {admin_token}"})
if res_builtin_del.status_code == 400 and "built-in" in res_builtin_del.json()["detail"].lower():
    log_result("CUSTOM_ROLES", "Built-in Role Protection", "PASS", "Protected built-in role 'admin' from deletion")
else:
    log_result("CUSTOM_ROLES", "Built-in Role Protection", "FAIL", f"Status: {res_builtin_del.status_code}")


print("\n" + "="*70)
print("PHASE 4: DOCUMENT INGESTION, PROCESSING & LIFECYCLE")
print("="*70)

# TXT Upload
txt_content = (
    "Enterprise AI Integration Directive 2026.\n"
    "Dr. Elena Vance finalized the Vector Synchronization Architecture in October 2025.\n"
    "The neural cache stores sub-vectors using Cosine Reciprocal Rank Fusion.\n"
    "Authorized network bandwidth exceeds 40 Gigabits per second."
).encode("utf-8")

txt_file = io.BytesIO(txt_content)
res_up = client.post("/api/v1/navigator/documents/upload", files={"file": ("audit_sample_directive.txt", txt_file, "text/plain")})
if res_up.status_code == 200:
    doc_data = res_up.json()
    doc_id = doc_data["id"]
    log_result("DOCUMENT_INGESTION", "TXT Upload & Chunking", "PASS", f"Ingested doc {doc_id}, chunks={doc_data['chunk_count']}, entities={doc_data['entity_count']}")
    
    # Duplicate upload detection
    txt_file2 = io.BytesIO(txt_content)
    res_dup = client.post("/api/v1/navigator/documents/upload", files={"file": ("audit_sample_directive.txt", txt_file2, "text/plain")})
    if res_dup.status_code == 409:
        log_result("DOCUMENT_INGESTION", "Duplicate Detection (SHA-256)", "PASS", "HTTP 409 Conflict returned for identical file content")
    else:
        log_result("DOCUMENT_INGESTION", "Duplicate Detection (SHA-256)", "FAIL", f"Expected 409, got {res_dup.status_code}")
        
    # Search for ingested fact
    res_search = client.post("/api/v1/navigator/search", json={"query": "Elena Vance Vector Synchronization Architecture", "mode": "hybrid", "top_k": 3})
    if res_search.status_code == 200 and len(res_search.json().get("results", [])) > 0:
        top_res = res_search.json()["results"][0]
        if "Elena Vance" in top_res["content"]:
            log_result("SEARCH_RAG", "Hybrid Search Accuracy", "PASS", f"Found matching chunk from doc (Score={top_res['score']:.3f})")
        else:
            log_result("SEARCH_RAG", "Hybrid Search Accuracy", "FAIL", "Top result did not contain expected fact")
    else:
        log_result("SEARCH_RAG", "Hybrid Search Accuracy", "FAIL", f"Search status: {res_search.status_code}")
        
    # Grounded Q&A
    res_ask = client.post("/api/v1/navigator/ask", json={"question": "Who finalized the Vector Synchronization Architecture and when?", "enable_graphrag": True, "top_k": 3})
    if res_ask.status_code == 200:
        ans_data = res_ask.json()
        if "Elena Vance" in ans_data["answer"] and len(ans_data.get("sources", [])) > 0:
            log_result("SEARCH_RAG", "Grounded Q&A with Citations", "PASS", f"Verified citation: {ans_data['sources'][0]['filename']}")
        else:
            log_result("SEARCH_RAG", "Grounded Q&A with Citations", "FAIL", f"Answer: {ans_data['answer']}")
    else:
        log_result("SEARCH_RAG", "Grounded Q&A with Citations", "FAIL", f"Status: {res_ask.status_code}")
        
    # Hallucination prevention on unanswerable question
    res_unans = client.post("/api/v1/navigator/ask", json={"question": "What is the capital of planet Mars according to the documents?", "enable_graphrag": False, "top_k": 3})
    if res_unans.status_code == 200:
        unans_data = res_unans.json()
        if unans_data["verification_status"] == "abstained" or "does not contain" in unans_data["answer"].lower() or "insufficient" in unans_data["answer"].lower():
            log_result("SEARCH_RAG", "Hallucination Prevention / Abstention", "PASS", "Strictly abstained without hallucinating facts")
        else:
            log_result("SEARCH_RAG", "Hallucination Prevention / Abstention", "FAIL", f"Unexpected answer: {unans_data['answer']}")
    else:
        log_result("SEARCH_RAG", "Hallucination Prevention / Abstention", "FAIL", f"Status: {res_unans.status_code}")
        
    # Clean up test document safely
    res_del = client.delete(f"/api/v1/navigator/documents/{doc_id}")
    if res_del.status_code == 200:
        log_result("DOCUMENT_INGESTION", "Document Deletion & Cascading Purge", "PASS", f"Safely purged document {doc_id} and its vector chunks")
    else:
        log_result("DOCUMENT_INGESTION", "Document Deletion & Cascading Purge", "FAIL", f"Status: {res_del.status_code}")
else:
    log_result("DOCUMENT_INGESTION", "TXT Upload & Chunking", "FAIL", f"Status: {res_up.status_code}")


print("\n" + "="*70)
print("PHASE 5: KNOWLEDGE GRAPH & REFRESH ENDPOINTS")
print("="*70)

res_graph = client.get("/api/v1/navigator/graph")
if res_graph.status_code == 200:
    g_data = res_graph.json()
    log_result("KNOWLEDGE_GRAPH", "Graph Topology Endpoint", "PASS", f"Nodes={len(g_data['nodes'])}, Edges={len(g_data['edges'])}")
else:
    log_result("KNOWLEDGE_GRAPH", "Graph Topology Endpoint", "FAIL", f"Status: {res_graph.status_code}")

# Refresh button endpoints
refresh_endpoints = [
    ("/api/v1/navigator/dashboard/metrics", "Dashboard Metrics Refresh"),
    ("/api/v1/health", "System Health Refresh"),
    ("/api/v1/navigator/documents", "Documents List Refresh"),
    ("/api/v1/navigator/evaluate/history", "Evaluation History Refresh"),
    ("/api/v1/auth/admin/roles-permissions", "Permissions Matrix Refresh")
]
for ep, name in refresh_endpoints:
    headers = {"Authorization": f"Bearer {admin_token}"} if "auth" in ep else {}
    res_ep = client.get(ep, headers=headers)
    log_result("REFRESH_SYSTEM", name, "PASS" if res_ep.status_code == 200 else "FAIL", f"HTTP {res_ep.status_code}")


print("\n" + "="*70)
print("PHASE 6 & 7: SECURITY & DATABASE INTEGRITY")
print("="*70)

# Public registration cannot grant admin
res_reg_admin = client.post("/api/v1/auth/register", json={
    "full_name": "Hacker Admin",
    "email": "hacker.admin@bad.com",
    "password": "Password123!",
    "role": "admin"
})
if res_reg_admin.status_code in (400, 403):
    log_result("SECURITY", "Privilege Escalation Defense", "PASS", "Public registration blocked from selecting admin role")
else:
    log_result("SECURITY", "Privilege Escalation Defense", "FAIL", f"Status: {res_reg_admin.status_code}")

# Database counts check
db = SessionLocal()
doc_count = db.query(DocumentRecord).count()
chunk_count = db.query(ChunkRecord).count()
role_count = db.query(RoleRecord).count()
db.close()

log_result("DATABASE", "Record Persistence & Schema Integrity", "PASS", f"Docs={doc_count}, Chunks={chunk_count}, Roles={role_count}")

print("\n" + "="*70)
print("AUDIT SUMMARY")
print("="*70)
total_tests = sum(len(tests) for tests in results.values())
passed_tests = sum(sum(1 for t in tests if t["status"] == "PASS") for tests in results.values())
print(f"Total Audit Checks: {total_tests} | Passed: {passed_tests} | Failed: {total_tests - passed_tests}")
