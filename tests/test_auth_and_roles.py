"""
Automated Integration Tests for Authentication, Public Registration Security,
and Role-Based Access Control.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)


def test_default_seeded_accounts_login():
    """Verify default seeded accounts can authenticate and return verified roles."""
    # 1. Admin login
    res_admin = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert "access_token" in data_admin
    assert data_admin["user"]["role"] == "admin"
    assert data_admin["user"]["email"] == "admin@eknavigator.com"

    # 2. Knowledge Worker login
    res_worker = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "worker@eknavigator.com", "password": "Worker@123456"}
    )
    assert res_worker.status_code == 200
    assert res_worker.json()["user"]["role"] == "knowledge_worker"

    # 3. Analyst login
    res_analyst = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "analyst@eknavigator.com", "password": "Analyst@123456"}
    )
    assert res_analyst.status_code == 200
    assert res_analyst.json()["user"]["role"] == "analyst"


def test_invalid_credentials_rejected():
    """Verify that wrong passwords and invalid accounts are rejected with 401."""
    res = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "WrongPassword999!"}
    )
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()

    res_unknown = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "nonexistent_user@eknavigator.com", "password": "Password@123"}
    )
    assert res_unknown.status_code == 401


def test_public_registration_allowed_roles():
    """Verify public visitors can register as Knowledge Worker or Analyst."""
    reg_worker = {
        "full_name": "New Registered Worker",
        "email": "new_worker_test@enterprise.com",
        "password": "SecurePassword123!",
        "organization": "Engineering Team",
        "role": "knowledge_worker"
    }
    res = client.post(f"{settings.API_V1_STR}/auth/register", json=reg_worker)
    assert res.status_code in [200, 409] # 409 if already registered from earlier run
    if res.status_code == 200:
        data = res.json()
        assert data["user"]["role"] == "knowledge_worker"
        assert "access_token" in data

    reg_analyst = {
        "full_name": "New Registered Analyst",
        "email": "new_analyst_test@enterprise.com",
        "password": "SecurePassword123!",
        "organization": "Data Science Hub",
        "role": "analyst"
    }
    res_a = client.post(f"{settings.API_V1_STR}/auth/register", json=reg_analyst)
    assert res_a.status_code in [200, 409]
    if res_a.status_code == 200:
        assert res_a.json()["user"]["role"] == "analyst"


def test_public_registration_admin_strictly_blocked():
    """Verify security constraint: public visitors CANNOT self-register as Administrator."""
    bad_payload = {
        "full_name": "Attacker Trying Admin",
        "email": "hacker@malicious.com",
        "password": "Password123!",
        "organization": "Evil Corp",
        "role": "admin"
    }
    res = client.post(f"{settings.API_V1_STR}/auth/register", json=bad_payload)
    assert res.status_code == 403
    assert "strictly prohibited" in res.json()["detail"].lower()


def test_auth_me_endpoint_requires_valid_token():
    """Verify /auth/me returns caller profile with valid token, rejects unauthenticated."""
    # Without token
    res_anon = client.get(f"{settings.API_V1_STR}/auth/me")
    assert res_anon.status_code == 401

    # With Admin token
    login_res = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    token = login_res.json()["access_token"]
    res_me = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "admin@eknavigator.com"
    assert res_me.json()["role"] == "admin"


def test_admin_user_management_authorization():
    """Verify user management endpoints are restricted to Administrators only."""
    # 1. Login as Worker
    login_worker = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "worker@eknavigator.com", "password": "Worker@123456"}
    )
    worker_token = login_worker.json()["access_token"]

    # Worker trying to list users -> 403 Forbidden
    res_forbidden = client.get(
        f"{settings.API_V1_STR}/auth/users",
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    assert res_forbidden.status_code == 403

    # 2. Login as Admin
    login_admin = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    admin_token = login_admin.json()["access_token"]

    # Admin listing users -> 200 OK
    res_allowed = client.get(
        f"{settings.API_V1_STR}/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_allowed.status_code == 200
    users = res_allowed.json()
    assert len(users) >= 3

    # Admin provisioning a new user
    provision_payload = {
        "full_name": "Provisioned Operations Staff",
        "email": "provisioned_staff_test@eknavigator.com",
        "password": "StaffPassword@123",
        "role": "knowledge_worker",
        "organization": "Enterprise Logistics"
    }
    prov_res = client.post(
        f"{settings.API_V1_STR}/auth/users/provision",
        json=provision_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert prov_res.status_code in [200, 409]


def test_forgot_password_otp_and_recovery_workflow():
    """Verify end-to-end OTP password reset workflow including rate limits and verification."""
    from backend.app.core.database import SessionLocal
    from backend.app.models.user import PasswordResetOTPRecord
    from backend.app.services.notification_delivery import hash_otp

    test_email = "otp_test_user@eknavigator.com"
    # Ensure test user exists
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "full_name": "OTP Test Subject",
            "email": test_email,
            "password": "InitialPassword@123",
            "role": "knowledge_worker",
            "organization": "Security Testing",
            "phone_number": "+15551234567"
        }
    )
    assert reg_res.status_code in [200, 409]

    # 1. Non-existent user request rejected
    res_404 = client.post(
        f"{settings.API_V1_STR}/auth/forgot-password/request",
        json={"email": "nonexistent_ghost@eknavigator.com", "delivery_method": "email"}
    )
    assert res_404.status_code == 404

    # 2. Valid user requests OTP
    req_res = client.post(
        f"{settings.API_V1_STR}/auth/forgot-password/request",
        json={"email": test_email, "delivery_method": "email"}
    )
    # May be 200 or 429 if recently requested
    if req_res.status_code == 429:
        # Cooldown active, wait or inspect existing
        pass
    else:
        assert req_res.status_code == 200
        data = req_res.json()
        assert "request_id" in data
        assert data["cooldown_seconds"] == 60
        req_id = data["request_id"]

        # 3. Rate limiting cooldown prevents immediate duplicate spam
        dup_res = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password/request",
            json={"email": test_email, "delivery_method": "email"}
        )
        assert dup_res.status_code == 429

        # 4. Bad OTP code is rejected
        bad_verify = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password/verify",
            json={"reset_request_id": req_id, "otp_code": "000000"}
        )
        assert bad_verify.status_code == 400

        # 5. Overwrite with known OTP in DB for deterministic verification test
        test_otp = "852963"
        session = SessionLocal()
        try:
            record = session.query(PasswordResetOTPRecord).filter(PasswordResetOTPRecord.id == req_id).first()
            if record:
                record.otp_hash = hash_otp(test_otp)
                session.commit()
        finally:
            session.close()

        # 6. Verify valid OTP code
        good_verify = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password/verify",
            json={"reset_request_id": req_id, "otp_code": test_otp}
        )
        assert good_verify.status_code == 200
        verify_data = good_verify.json()
        assert "reset_token" in verify_data
        reset_token = verify_data["reset_token"]

        # 7. Update password with reset token
        new_pwd = "UpdatedPassword@456"
        reset_res = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password/reset",
            json={
                "reset_token": reset_token,
                "new_password": new_pwd,
                "confirm_password": new_pwd
            }
        )
        assert reset_res.status_code == 200

        # 8. Authenticate with new password
        login_new = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": test_email, "password": new_pwd}
        )
        assert login_new.status_code == 200


def test_admin_roles_matrix_and_audit_logs():
    """Verify roles matrix and audit logs endpoints enforce admin authorization."""
    # Worker login
    worker_login = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "worker@eknavigator.com", "password": "Worker@123456"}
    )
    worker_token = worker_login.json()["access_token"]

    # Admin login
    admin_login = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    admin_token = admin_login.json()["access_token"]

    # 1. Roles & Permissions Matrix
    # Worker blocked -> 403
    w_roles = client.get(
        f"{settings.API_V1_STR}/auth/admin/roles-permissions",
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    assert w_roles.status_code == 403

    # Admin allowed -> 200
    a_roles = client.get(
        f"{settings.API_V1_STR}/auth/admin/roles-permissions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert a_roles.status_code == 200
    matrix = a_roles.json()
    assert len(matrix) >= 5
    assert any(m["capability"] == "System Administration" for m in matrix)

    # 2. Operational Audit Logs
    # Worker blocked -> 403
    w_audit = client.get(
        f"{settings.API_V1_STR}/auth/admin/audit-logs",
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    assert w_audit.status_code == 403

    # Admin allowed -> 200
    a_audit = client.get(
        f"{settings.API_V1_STR}/auth/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert a_audit.status_code == 200
    logs = a_audit.json()
    assert isinstance(logs, list)


def test_document_preview_and_download_endpoints():
    """Verify document preview and download endpoints return authentic file content."""
    # First get document list
    docs_res = client.get(f"{settings.API_V1_STR}/navigator/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()["documents"]

    if docs:
        doc_id = docs[0]["id"]
        # 1. Preview
        prev_res = client.get(f"{settings.API_V1_STR}/navigator/documents/{doc_id}/preview")
        assert prev_res.status_code == 200
        prev_data = prev_res.json()
        assert "filename" in prev_data
        assert "pages" in prev_data
        assert len(prev_data["pages"]) >= 1

        # 2. Download
        dl_res = client.get(f"{settings.API_V1_STR}/navigator/documents/{doc_id}/download")
        assert dl_res.status_code == 200
        assert dl_res.headers.get("content-disposition") is not None
        assert len(dl_res.content) > 0


def test_my_permissions_endpoint():
    """Verify /auth/my-permissions returns tailored capabilities for each role."""
    # 1. Admin permissions
    res_adm = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    admin_token = res_adm.json()["access_token"]
    perm_adm = client.get(
        f"{settings.API_V1_STR}/auth/my-permissions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert perm_adm.status_code == 200
    adm_data = perm_adm.json()
    assert adm_data["role_id"] == "admin"
    assert "system_admin" in adm_data["permissions"]
    assert "audit_logs" in adm_data["permissions"]

    # 2. Worker permissions
    res_w = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "worker@eknavigator.com", "password": "Worker@123456"}
    )
    worker_token = res_w.json()["access_token"]
    perm_w = client.get(
        f"{settings.API_V1_STR}/auth/my-permissions",
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    assert perm_w.status_code == 200
    w_data = perm_w.json()
    assert w_data["role_id"] == "knowledge_worker"
    assert "system_admin" not in w_data["permissions"]
    assert "doc_ingestion" in w_data["permissions"]

    # 3. Analyst permissions
    res_a = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "analyst@eknavigator.com", "password": "Analyst@123456"}
    )
    analyst_token = res_a.json()["access_token"]
    perm_a = client.get(
        f"{settings.API_V1_STR}/auth/my-permissions",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert perm_a.status_code == 200
    a_data = perm_a.json()
    assert a_data["role_id"] == "analyst"
    assert "knowledge_graph" in a_data["permissions"]
    assert "system_admin" not in a_data["permissions"]


def test_admin_capabilities_and_roles_list():
    """Verify capabilities list and roles listing with access control."""
    login_adm = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    admin_token = login_adm.json()["access_token"]

    login_w = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "worker@eknavigator.com", "password": "Worker@123456"}
    )
    worker_token = login_w.json()["access_token"]

    # Capabilities endpoint
    cap_forbidden = client.get(
        f"{settings.API_V1_STR}/auth/admin/capabilities",
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    assert cap_forbidden.status_code == 403

    cap_res = client.get(
        f"{settings.API_V1_STR}/auth/admin/capabilities",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert cap_res.status_code == 200
    caps = cap_res.json()
    assert len(caps) == 11
    cap_ids = {c["id"] for c in caps}
    assert "system_admin" in cap_ids
    assert "search_retrieval" in cap_ids

    # Roles endpoint
    roles_forbidden = client.get(
        f"{settings.API_V1_STR}/auth/admin/roles",
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    assert roles_forbidden.status_code == 403

    roles_res = client.get(
        f"{settings.API_V1_STR}/auth/admin/roles",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert roles_res.status_code == 200
    roles = roles_res.json()
    assert len(roles) >= 3
    role_ids = {r["id"] for r in roles}
    assert "admin" in role_ids
    assert "knowledge_worker" in role_ids
    assert "analyst" in role_ids


def test_custom_role_crud_lifecycle_and_guards():
    """Verify complete CRUD lifecycle of a custom role with built-in guardrails."""
    login_adm = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    admin_token = login_adm.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Guard: Cannot create role with conflicting built-in name
    res_conflict = client.post(
        f"{settings.API_V1_STR}/auth/admin/roles",
        json={"name": "Administrator", "permissions": ["system_admin"]},
        headers=headers
    )
    assert res_conflict.status_code == 400

    # 2. Guard: Cannot provide invalid permission capabilities
    res_invalid_perm = client.post(
        f"{settings.API_V1_STR}/auth/admin/roles",
        json={"name": "Test Role", "permissions": ["super_laser_beam_access"]},
        headers=headers
    )
    assert res_invalid_perm.status_code == 400

    # 3. Create valid custom role
    import uuid
    unique_role_name = f"Compliance Auditor {uuid.uuid4().hex[:6]}"
    create_res = client.post(
        f"{settings.API_V1_STR}/auth/admin/roles",
        json={
            "name": unique_role_name,
            "description": "Reviews operational audit logs and evaluation benchmarks.",
            "permissions": ["audit_logs", "search_retrieval", "evaluation", "profile_settings"]
        },
        headers=headers
    )
    assert create_res.status_code == 201
    created_role = create_res.json()
    assert created_role["name"] == unique_role_name
    assert created_role["is_builtin"] is False
    assert "audit_logs" in created_role["permissions"]
    role_id = created_role["id"]

    # 4. Update the custom role
    update_res = client.put(
        f"{settings.API_V1_STR}/auth/admin/roles/{role_id}",
        json={
            "description": "Updated auditor description",
            "permissions": ["audit_logs", "search_retrieval", "evaluation", "export_center", "profile_settings"]
        },
        headers=headers
    )
    assert update_res.status_code == 200
    updated_role = update_res.json()
    assert "export_center" in updated_role["permissions"]
    assert updated_role["description"] == "Updated auditor description"

    # 5. Guard: Cannot rename or delete built-in roles
    rename_builtin = client.put(
        f"{settings.API_V1_STR}/auth/admin/roles/admin",
        json={"name": "Super Admin New Name"},
        headers=headers
    )
    assert rename_builtin.status_code == 400
    assert "built-in" in rename_builtin.json()["detail"].lower()

    delete_builtin = client.delete(
        f"{settings.API_V1_STR}/auth/admin/roles/admin",
        headers=headers
    )
    assert delete_builtin.status_code == 400
    assert "built-in" in delete_builtin.json()["detail"].lower()

    # 6. Delete unassigned custom role
    del_res = client.delete(
        f"{settings.API_V1_STR}/auth/admin/roles/{role_id}",
        headers=headers
    )
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm deletion
    get_res = client.get(f"{settings.API_V1_STR}/auth/admin/roles", headers=headers)
    assert all(r["id"] != role_id for r in get_res.json())


def test_custom_role_user_assignment_and_assigned_deletion_guard():
    """Verify assigning a custom role to a user and guard preventing deleting assigned roles."""
    login_adm = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "admin@eknavigator.com", "password": "Admin@123456"}
    )
    admin_token = login_adm.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    import uuid
    role_name = f"Assigned Specialist {uuid.uuid4().hex[:6]}"
    create_role = client.post(
        f"{settings.API_V1_STR}/auth/admin/roles",
        json={
            "name": role_name,
            "description": "Test role with user assignment guard.",
            "permissions": ["search_retrieval", "qa_citations"]
        },
        headers=headers
    )
    assert create_role.status_code == 201
    custom_role_id = create_role.json()["id"]

    # Provision user with this custom role
    user_email = f"specialist_{uuid.uuid4().hex[:6]}@eknavigator.com"
    prov_res = client.post(
        f"{settings.API_V1_STR}/auth/users/provision",
        json={
            "full_name": "Assigned Specialist User",
            "email": user_email,
            "password": "SpecialistPassword@123",
            "role": custom_role_id,
            "organization": "Specialist Ops"
        },
        headers=headers
    )
    assert prov_res.status_code == 200
    assert prov_res.json()["role"] == custom_role_id

    # Try deleting role while assigned -> MUST BE BLOCKED with 400
    del_blocked = client.delete(
        f"{settings.API_V1_STR}/auth/admin/roles/{custom_role_id}",
        headers=headers
    )
    assert del_blocked.status_code == 400
    assert "assigned" in del_blocked.json()["detail"].lower()

    # Reassign user back to worker
    user_id = prov_res.json()["id"]
    reassign_res = client.patch(
        f"{settings.API_V1_STR}/auth/users/{user_id}/status",
        json={"role": "knowledge_worker"},
        headers=headers
    )
    assert reassign_res.status_code == 200

    # Now deletion must succeed
    del_ok = client.delete(
        f"{settings.API_V1_STR}/auth/admin/roles/{custom_role_id}",
        headers=headers
    )
    assert del_ok.status_code == 200

