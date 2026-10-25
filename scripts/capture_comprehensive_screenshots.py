import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def capture_all():
    screenshot_dir = Path("enterprise-knowledge-navigator/docs/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    print("[*] Launching Chrome via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        # Helper to make sure view is fully loaded
        def capture_page(page, filename, desc):
            page.wait_for_timeout(1000)
            target = screenshot_dir / filename
            page.screenshot(path=str(target))
            print(f"  [+] Captured {filename}: {desc} ({target.stat().st_size} bytes)")

        # =========================================================================
        # SECTION A: LOGIN & AUTHENTICATION
        # =========================================================================
        print("\n--- SECTION A: LOGIN & AUTHENTICATION ---")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(1000)
        capture_page(page, "01_landing_hero.png", "Landing Page & System Architecture Overview")
        
        # Open Login Modal
        page.click("#navLoginBtn")
        page.wait_for_selector("#loginModal", state="visible")
        page.wait_for_timeout(800)
        capture_page(page, "02_login_modal.png", "Login Portal Modal with 3 One-Click Role Presets")
        
        # Open Forgot Password Modal
        page.click("#forgotPasswordLink")
        page.wait_for_selector("#forgotPasswordModal", state="visible")
        page.wait_for_timeout(800)
        capture_page(page, "03_forgot_password_modal.png", "Self-Service Password Recovery Dialog")
        page.click("#closeForgotModalBtn")
        page.wait_for_timeout(500)
        
        ctx.close()

        # =========================================================================
        # SECTION B: ADMINISTRATOR ROLE WALKTHROUGH
        # =========================================================================
        print("\n--- SECTION B: ADMINISTRATOR ROLE WALKTHROUGH ---")
        ctx_admin = browser.new_context(viewport={"width": 1440, "height": 900})
        page_admin = ctx_admin.new_page()
        page_admin.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page_admin.click("#navLoginBtn")
        page_admin.wait_for_selector("#loginModal", state="visible")
        page_admin.click("#demoAdminBtn")
        page_admin.wait_for_timeout(400)
        page_admin.click("#loginSubmitBtn")
        page_admin.wait_for_selector("#authenticatedAppView", state="visible")
        page_admin.wait_for_timeout(2000)
        
        # 1. Admin Dashboard
        capture_page(page_admin, "admin_01_dashboard.png", "Admin Executive Dashboard & System KPI Cards")
        
        # 2. Document Library & Ingestion
        page_admin.click('.sidebar-nav a[data-view="documents"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_02_documents.png", "Document Management & Ingestion Center")
        
        # Document Preview Modal (click first preview button if available)
        try:
            preview_btns = page_admin.query_selector_all(".btn-preview-doc")
            if preview_btns:
                preview_btns[0].click()
                page_admin.wait_for_selector("#documentPreviewModal", state="visible")
                page_admin.wait_for_timeout(1000)
                capture_page(page_admin, "admin_03_doc_preview_modal.png", "Document Preview & Metadata Inspection Modal")
                page_admin.click("#closeDocPreviewModalBtn")
                page_admin.wait_for_timeout(500)
        except Exception as e:
            print("  [-] Could not open doc preview modal:", e)

        # 3. Hybrid Search & Retrieval
        page_admin.click('.sidebar-nav a[data-view="search"]')
        page_admin.wait_for_timeout(1000)
        # Type search query and search
        page_admin.fill("#searchQueryInput", "enterprise remote work security policy")
        page_admin.click("#executeSearchBtn")
        page_admin.wait_for_timeout(2000)
        capture_page(page_admin, "admin_04_hybrid_search.png", "Hybrid Search (BM25 + TF-IDF Cosine + RRF Fusion)")

        # 4. Ask AI / Grounded Assistant
        page_admin.click('.sidebar-nav a[data-view="assistant"]')
        page_admin.wait_for_timeout(1000)
        # Ask question if empty
        page_admin.fill("#chatInput", "What are the security guidelines for remote work and VPN access?")
        page_admin.click("#sendChatBtn")
        page_admin.wait_for_timeout(3500)
        capture_page(page_admin, "admin_05_grounded_assistant.png", "Grounded Assistant with Verified Institutional Citations")

        # 5. Collections & Folders
        page_admin.click('.sidebar-nav a[data-view="collections"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_06_collections.png", "Enterprise Collections & Research Folders")

        # Create Collection Modal
        try:
            page_admin.click("#openCreateColModalBtn")
            page_admin.wait_for_selector("#createCollectionModal", state="visible")
            page_admin.wait_for_timeout(800)
            capture_page(page_admin, "admin_07_create_collection_modal.png", "Create Collection Workspace Dialog")
            page_admin.click("#closeCreateColModalBtn")
            page_admin.wait_for_timeout(500)
        except Exception as e:
            print("  [-] Could not open create collection modal:", e)

        # 6. Saved Insights
        page_admin.click('.sidebar-nav a[data-view="saved"]')
        page_admin.wait_for_timeout(1200)
        capture_page(page_admin, "admin_08_saved_insights.png", "Saved Intelligence & Bookmarked Answers")

        # 7. Enterprise Knowledge Graph
        page_admin.click('.sidebar-nav a[data-view="graph"]')
        page_admin.wait_for_timeout(4000) # Wait for D3 force simulation
        capture_page(page_admin, "admin_09_knowledge_graph.png", "Enterprise Knowledge Graph & GraphRAG Entity Exploration")

        # 8. Evaluation & Benchmarks
        page_admin.click('.sidebar-nav a[data-view="evaluation"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_10_evaluation.png", "Quality Evaluation Benchmarks (Precision, Recall, MRR, Latency)")

        # 9. User Directory & Management
        page_admin.click('.sidebar-nav a[data-view="users"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_11_users_directory.png", "User Management & Role Assignment Directory")

        # Provision User Modal
        try:
            page_admin.click("#openProvisionUserModalBtn")
            page_admin.wait_for_selector("#provisionUserModal", state="visible")
            page_admin.wait_for_timeout(800)
            capture_page(page_admin, "admin_12_provision_user_modal.png", "Provision New User Account Form & Role Selection")
            page_admin.click("#closeProvisionModalBtn")
            page_admin.wait_for_timeout(500)
        except Exception as e:
            print("  [-] Could not open provision user modal:", e)

        # 10. Roles & Permissions Matrix
        page_admin.click('.sidebar-nav a[data-view="roles"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_13_roles_matrix.png", "Granular 11-Point Roles & Permissions Matrix")

        # Custom Role Modal
        try:
            page_admin.click("#openCreateRoleModalBtn")
            page_admin.wait_for_selector("#customRoleModal", state="visible")
            page_admin.wait_for_timeout(800)
            capture_page(page_admin, "admin_14_custom_role_modal.png", "Create Dynamic Custom Security Role Dialog")
            page_admin.click("#closeCustomRoleModalBtn")
            page_admin.wait_for_timeout(500)
        except Exception as e:
            print("  [-] Could not open custom role modal:", e)

        # 11. Reports & Data Export Center
        page_admin.click('.sidebar-nav a[data-view="reports"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_15_reports_export.png", "Institutional Reports & Compliance Data Export Center")

        # 12. Operational Audit Logs
        page_admin.click('.sidebar-nav a[data-view="audit"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_16_audit_logs.png", "Immutable Operational Audit Logs & Security Telemetry")

        # 13. System Architecture & Health
        page_admin.click('.sidebar-nav a[data-view="system"]')
        page_admin.wait_for_timeout(1500)
        capture_page(page_admin, "admin_17_system_health.png", "System Architecture, Resource Telemetry & Health Checks")

        # 14. Notifications
        page_admin.click('.sidebar-nav a[data-view="notifications"]')
        page_admin.wait_for_timeout(1200)
        capture_page(page_admin, "admin_18_notifications.png", "Platform Security & Administrative Notifications")

        # 15. Profile
        page_admin.click('.sidebar-nav a[data-view="profile"]')
        page_admin.wait_for_timeout(1200)
        capture_page(page_admin, "admin_19_profile.png", "User Profile, Active Clearance & Security Credentials")

        ctx_admin.close()

        # =========================================================================
        # SECTION C: KNOWLEDGE WORKER ROLE WALKTHROUGH
        # =========================================================================
        print("\n--- SECTION C: KNOWLEDGE WORKER ROLE WALKTHROUGH ---")
        ctx_worker = browser.new_context(viewport={"width": 1440, "height": 900})
        page_worker = ctx_worker.new_page()
        page_worker.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page_worker.click("#navLoginBtn")
        page_worker.wait_for_selector("#loginModal", state="visible")
        page_worker.click("#demoWorkerBtn")
        page_worker.wait_for_timeout(400)
        page_worker.click("#loginSubmitBtn")
        page_worker.wait_for_selector("#authenticatedAppView", state="visible")
        page_worker.wait_for_timeout(2000)

        # 1. Worker Dashboard (Scoped to department)
        capture_page(page_worker, "worker_01_dashboard.png", "Knowledge Worker Department-Scoped Dashboard")

        # 2. Worker Document Library
        page_worker.click('.sidebar-nav a[data-view="documents"]')
        page_worker.wait_for_timeout(1500)
        capture_page(page_worker, "worker_02_documents.png", "Knowledge Worker Document Library (Clearance-Filtered)")

        # 3. Worker Assistant
        page_worker.click('.sidebar-nav a[data-view="assistant"]')
        page_worker.wait_for_timeout(1500)
        capture_page(page_worker, "worker_03_assistant.png", "Knowledge Worker Grounded Assistant with Strict Department Scoping")

        # 4. Worker Collections
        page_worker.click('.sidebar-nav a[data-view="collections"]')
        page_worker.wait_for_timeout(1200)
        capture_page(page_worker, "worker_04_collections.png", "Knowledge Worker Personal Workspace & Collections")

        # 5. Worker Sidebar & Role Restrictions (showing absence of Admin items)
        capture_page(page_worker, "worker_05_sidebar_rbac.png", "Knowledge Worker Sidebar Demonstrating Strict RBAC Navigation Isolation")

        ctx_worker.close()

        # =========================================================================
        # SECTION D: KNOWLEDGE ANALYST ROLE WALKTHROUGH
        # =========================================================================
        print("\n--- SECTION D: KNOWLEDGE ANALYST ROLE WALKTHROUGH ---")
        ctx_analyst = browser.new_context(viewport={"width": 1440, "height": 900})
        page_analyst = ctx_analyst.new_page()
        page_analyst.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page_analyst.click("#navLoginBtn")
        page_analyst.wait_for_selector("#loginModal", state="visible")
        page_analyst.click("#demoAnalystBtn")
        page_analyst.wait_for_timeout(400)
        page_analyst.click("#loginSubmitBtn")
        page_analyst.wait_for_selector("#authenticatedAppView", state="visible")
        page_analyst.wait_for_timeout(2000)

        # 1. Analyst Dashboard
        capture_page(page_analyst, "analyst_01_dashboard.png", "Knowledge Analyst Institutional Overview Dashboard")

        # 2. Analyst Knowledge Graph
        page_analyst.click('.sidebar-nav a[data-view="graph"]')
        page_analyst.wait_for_timeout(4000)
        capture_page(page_analyst, "analyst_02_graph.png", "Knowledge Analyst GraphRAG Co-Occurrence Entity Graph")

        # 3. Analyst Evaluation Benchmarks
        page_analyst.click('.sidebar-nav a[data-view="evaluation"]')
        page_analyst.wait_for_timeout(1500)
        capture_page(page_analyst, "analyst_03_evaluation.png", "Knowledge Analyst Retrieval Quality & Groundedness Benchmarks")

        # 4. Analyst Reports & Data Export
        page_analyst.click('.sidebar-nav a[data-view="reports"]')
        page_analyst.wait_for_timeout(1500)
        capture_page(page_analyst, "analyst_04_reports.png", "Knowledge Analyst Intelligence Synthesis & Report Generation")

        ctx_analyst.close()

        browser.close()
        print("\n[SUCCESS] All screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
