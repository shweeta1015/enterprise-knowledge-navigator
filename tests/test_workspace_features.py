"""
Comprehensive Automated Tests for Enterprise Workspace Features:
- Collections & Categorization (Part 9)
- Search History & Saved Insights (Part 10)
- Notifications Center (Part 14)
- Personal Profile & User Settings (Part 15)
- Reports & Data Export Center (Part 16)
"""

import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)


def _get_auth_headers(email: str = "admin@eknavigator.com", password: str = "Admin@123456"):
    """Helper to authenticate and obtain Authorization Bearer headers."""
    res = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password, "remember_me": True}
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. COLLECTIONS & FOLDERS TESTS
# ============================================================================

def test_collections_crud_workflow():
    """Verify creating, listing, assigning docs, and deleting collections."""
    headers = _get_auth_headers()

    # 1. List collections (seeded default collections should exist)
    res = client.get(f"{settings.API_V1_STR}/workspace/collections")
    assert res.status_code == 200
    initial_cols = res.json()
    assert len(initial_cols) >= 1

    # 2. Create a new collection
    col_name = "Automated Test Project Folder"
    create_res = client.post(
        f"{settings.API_V1_STR}/workspace/collections",
        headers=headers,
        json={
            "name": col_name,
            "description": "Folder dedicated to automated verification testing.",
            "color": "#10B981",
            "icon": "🧪"
        }
    )
    assert create_res.status_code == 201
    created_col = create_res.json()
    assert created_col["name"] == col_name
    col_id = created_col["id"]

    # 3. Prevent duplicate collection name
    dup_res = client.post(
        f"{settings.API_V1_STR}/workspace/collections",
        headers=headers,
        json={"name": col_name, "description": "Duplicate name"}
    )
    assert dup_res.status_code == 409

    # 4. Assign document to collection if any documents exist
    docs_res = client.get(f"{settings.API_V1_STR}/navigator/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json().get("documents", [])
    if docs:
        target_doc_id = docs[0]["id"]
        assign_res = client.post(
            f"{settings.API_V1_STR}/workspace/collections/{col_id}/documents",
            headers=headers,
            json={"document_ids": [target_doc_id]}
        )
        assert assign_res.status_code == 200

        # Remove doc
        remove_res = client.delete(
            f"{settings.API_V1_STR}/workspace/collections/{col_id}/documents/{target_doc_id}",
            headers=headers
        )
        assert remove_res.status_code == 204

    # 5. Delete collection
    del_res = client.delete(
        f"{settings.API_V1_STR}/workspace/collections/{col_id}",
        headers=headers
    )
    assert del_res.status_code == 204


# ============================================================================
# 2. SAVED ANSWERS & BOOKMARKS TESTS
# ============================================================================

def test_saved_answers_workflow():
    """Verify saving Q&A answers, listing, updating notes, and deleting bookmarks."""
    headers = _get_auth_headers("worker@eknavigator.com", "Worker@123456")

    # 1. Save an answer
    save_payload = {
        "question": "What is the AES-256 requirement?",
        "answer": "All data at rest must use AES-256 encryption according to the security manual.",
        "mode": "rag",
        "confidence_score": 0.96,
        "citations": [{"filename": "governance.docx", "page_number": 1, "snippet": "AES-256 required"}],
        "entities": [{"name": "AES-256", "category": "TECH"}],
        "user_notes": "Important reference for Q3 audit."
    }
    create_res = client.post(
        f"{settings.API_V1_STR}/workspace/saved-answers",
        headers=headers,
        json=save_payload
    )
    assert create_res.status_code == 201
    saved_item = create_res.json()
    assert saved_item["question"] == save_payload["question"]
    saved_id = saved_item["id"]

    # 2. List saved answers
    list_res = client.get(
        f"{settings.API_V1_STR}/workspace/saved-answers",
        headers=headers
    )
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["id"] == saved_id for item in items)

    # 3. Update note
    note_res = client.patch(
        f"{settings.API_V1_STR}/workspace/saved-answers/{saved_id}/note",
        headers=headers,
        json={"user_notes": "Updated note: Verified with Chief Information Security Officer."}
    )
    assert note_res.status_code == 200
    assert "Chief Information Security Officer" in note_res.json()["user_notes"]

    # 4. Delete saved answer
    del_res = client.delete(
        f"{settings.API_V1_STR}/workspace/saved-answers/{saved_id}",
        headers=headers
    )
    assert del_res.status_code == 204


# ============================================================================
# 3. SEARCH HISTORY TESTS
# ============================================================================

def test_search_history_workflow():
    """Verify that searches record into search history and can be queried/cleared."""
    headers = _get_auth_headers()

    # Trigger a search
    client.post(
        f"{settings.API_V1_STR}/navigator/search",
        json={"query": "Automated Testing Query", "mode": "hybrid", "top_k": 3}
    )

    # Query search history
    hist_res = client.get(
        f"{settings.API_V1_STR}/workspace/search-history?limit=10",
        headers=headers
    )
    assert hist_res.status_code == 200
    records = hist_res.json()
    assert len(records) >= 1
    assert any(r["query_text"] == "Automated Testing Query" for r in records)


# ============================================================================
# 4. NOTIFICATIONS TESTS
# ============================================================================

def test_notifications_workflow():
    """Verify fetching notifications, unread counts, and marking as read."""
    headers = _get_auth_headers()

    # 1. Fetch notifications
    notifs_res = client.get(
        f"{settings.API_V1_STR}/workspace/notifications",
        headers=headers
    )
    assert notifs_res.status_code == 200
    data = notifs_res.json()
    assert "unread_count" in data
    assert "items" in data
    assert len(data["items"]) >= 1

    # 2. Mark single notification as read if items exist
    if data["items"]:
        first_id = data["items"][0]["id"]
        read_res = client.patch(
            f"{settings.API_V1_STR}/workspace/notifications/{first_id}/read",
            headers=headers
        )
        assert read_res.status_code == 200

    # 3. Mark all as read
    all_read_res = client.post(
        f"{settings.API_V1_STR}/workspace/notifications/mark-all-read",
        headers=headers
    )
    assert all_read_res.status_code == 200

    # Verify unread count is now 0
    after_res = client.get(
        f"{settings.API_V1_STR}/workspace/notifications",
        headers=headers
    )
    assert after_res.status_code == 200
    assert after_res.json()["unread_count"] == 0


# ============================================================================
# 5. USER PROFILE & PREFERENCES TESTS
# ============================================================================

def test_profile_and_preferences_workflow():
    """Verify fetching profile, updating organization/name, and modifying UI preferences."""
    import uuid
    new_email = f"profile_{str(uuid.uuid4())[:8]}@enterprise.com"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": new_email,
            "full_name": "Test Profile User",
            "password": "Password@123",
            "role": "analyst",
            "organization": "Data Labs"
        }
    )
    assert reg_res.status_code == 200
    headers = _get_auth_headers(new_email, "Password@123")

    # 1. Get profile me
    me_res = client.get(f"{settings.API_V1_STR}/workspace/profile/me", headers=headers)
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["email"] == new_email
    assert profile["full_name"] == "Test Profile User"
    assert "preferences" in profile

    # 2. Update display name & organization
    update_res = client.patch(
        f"{settings.API_V1_STR}/workspace/profile/update",
        headers=headers,
        json={"full_name": "Senior Profile User", "organization": "Global AI Research"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["user"]["full_name"] == "Senior Profile User"

    # 3. Update UI preferences
    pref_res = client.patch(
        f"{settings.API_V1_STR}/workspace/profile/preferences",
        headers=headers,
        json={"default_search_mode": "semantic", "default_top_k": 8, "graphrag_enabled": False}
    )
    assert pref_res.status_code == 200
    pref_data = pref_res.json()
    assert pref_data["default_search_mode"] == "semantic"
    assert pref_data["default_top_k"] == 8
    assert pref_data["graphrag_enabled"] is False

    # 4. Change password with wrong current password (should be rejected)
    wrong_pwd_res = client.post(
        f"{settings.API_V1_STR}/workspace/profile/change-password",
        headers=headers,
        json={"current_password": "WrongPassword!", "new_password": "NewSecret@123"}
    )
    assert wrong_pwd_res.status_code == 400

    # 5. Change password successfully
    change_res = client.post(
        f"{settings.API_V1_STR}/workspace/profile/change-password",
        headers=headers,
        json={"current_password": "Password@123", "new_password": "NewSecret@123"}
    )
    assert change_res.status_code == 200

    # Verify login with new password
    new_login_headers = _get_auth_headers(new_email, "NewSecret@123")
    assert "Authorization" in new_login_headers


# ============================================================================
# 6. REPORTS & DATA EXPORT TESTS
# ============================================================================

def test_data_export_endpoints():
    """Verify document inventory, evaluation runs, and audit logs CSV/JSON exports."""
    headers = _get_auth_headers()

    # 1. Documents export (CSV and JSON)
    doc_csv_res = client.get(
        f"{settings.API_V1_STR}/workspace/reports/export/documents?format=csv",
        headers=headers
    )
    assert doc_csv_res.status_code == 200
    assert "text/csv" in doc_csv_res.headers["content-type"]
    assert "Filename" in doc_csv_res.text

    doc_json_res = client.get(
        f"{settings.API_V1_STR}/workspace/reports/export/documents?format=json",
        headers=headers
    )
    assert doc_json_res.status_code == 200
    assert isinstance(doc_json_res.json(), list)

    # 2. Evaluation history export (CSV and JSON)
    eval_csv_res = client.get(
        f"{settings.API_V1_STR}/workspace/reports/export/evaluations?format=csv",
        headers=headers
    )
    assert eval_csv_res.status_code == 200
    assert "text/csv" in eval_csv_res.headers["content-type"]

    eval_json_res = client.get(
        f"{settings.API_V1_STR}/workspace/reports/export/evaluations?format=json",
        headers=headers
    )
    assert eval_json_res.status_code == 200
    assert isinstance(eval_json_res.json(), list)

    # 3. Audit logs export (CSV and JSON)
    logs_csv_res = client.get(
        f"{settings.API_V1_STR}/workspace/reports/export/audit-logs?format=csv",
        headers=headers
    )
    assert logs_csv_res.status_code == 200
    assert "text/csv" in logs_csv_res.headers["content-type"]

    logs_json_res = client.get(
        f"{settings.API_V1_STR}/workspace/reports/export/audit-logs?format=json",
        headers=headers
    )
    assert logs_json_res.status_code == 200
    assert isinstance(logs_json_res.json(), list)
