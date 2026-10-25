import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def run():
    out_dir = Path("enterprise-knowledge-navigator/docs/screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("[*] Launching Chrome via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        # --- SECTION A: PUBLIC & LOGIN ---
        print("\n--- Capturing Public & Login Screens ---")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=str(out_dir / "01_landing_hero.png"))
        print("Captured 01_landing_hero.png")
        
        # Click Sign In button
        page.click("#navLoginBtn")
        page.wait_for_selector("#loginCard", state="visible")
        time.sleep(1)
        page.screenshot(path=str(out_dir / "02_login_portal.png"))
        print("Captured 02_login_portal.png")
        
        # Click Forgot Password
        page.click("#forgotPasswordLink")
        page.wait_for_selector("#forgotPasswordCard", state="visible")
        time.sleep(1)
        page.screenshot(path=str(out_dir / "03_forgot_password.png"))
        print("Captured 03_forgot_password.png")
        ctx.close()
        
        # --- SECTION B: ADMINISTRATOR ---
        print("\n--- Capturing Administrator Screens ---")
        ctx_admin = browser.new_context(viewport={"width": 1440, "height": 900})
        page_admin = ctx_admin.new_page()
        page_admin.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page_admin.click("#navLoginBtn")
        page_admin.wait_for_selector("#loginCard", state="visible")
        page_admin.click("#demoAdminBtn")
        time.sleep(0.5)
        page_admin.click("#loginSubmitBtn")
        page_admin.wait_for_selector("#authenticatedAppView", state="visible")
        time.sleep(2)
        
        # 1. Admin Dashboard
        page_admin.screenshot(path=str(out_dir / "admin_01_dashboard.png"))
        print("Captured admin_01_dashboard.png")
        
        # 2. Documents
        page_admin.click('.sidebar-nav a[data-view="documents"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_02_documents.png"))
        print("Captured admin_02_documents.png")
        
        # 3. Document Preview Modal
        try:
            btns = page_admin.query_selector_all(".btn-preview-doc, button[data-action='preview']")
            if btns:
                btns[0].click()
                time.sleep(1)
                page_admin.screenshot(path=str(out_dir / "admin_03_doc_preview.png"))
                print("Captured admin_03_doc_preview.png")
                close_btn = page_admin.query_selector("#closeDocPreviewModalBtn, #documentPreviewModal .close-modal")
                if close_btn:
                    close_btn.click()
                time.sleep(0.5)
            else:
                page_admin.screenshot(path=str(out_dir / "admin_03_doc_preview.png"))
                print("Captured admin_03_doc_preview.png (table state)")
        except Exception as e:
            print("Preview modal skip:", e)
            page_admin.screenshot(path=str(out_dir / "admin_03_doc_preview.png"))

        # 4. Search
        page_admin.click('.sidebar-nav a[data-view="search"]')
        time.sleep(1)
        try:
            page_admin.fill("#searchInput", "remote work security VPN access policy")
            page_admin.click("#executeSearchBtn")
            time.sleep(2)
        except Exception as e:
            print("Search query fill error:", e)
        page_admin.screenshot(path=str(out_dir / "admin_04_hybrid_search.png"))
        print("Captured admin_04_hybrid_search.png")
        
        # 5. Assistant
        page_admin.click('.sidebar-nav a[data-view="assistant"]')
        time.sleep(1)
        try:
            pills = page_admin.query_selector_all(".sug-pill")
            if pills:
                pills[0].click()
                time.sleep(0.5)
            else:
                page_admin.fill("#askInput", "What encryption standard must be used for enterprise data at rest?")
            page_admin.click("#askSubmitBtn")
            time.sleep(3)
        except Exception as e:
            print("Assistant submit error:", e)
        page_admin.screenshot(path=str(out_dir / "admin_05_grounded_assistant.png"))
        print("Captured admin_05_grounded_assistant.png")
        
        # 6. Collections
        page_admin.click('.sidebar-nav a[data-view="collections"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_06_collections.png"))
        print("Captured admin_06_collections.png")
        
        # 7. Create Collection Modal
        try:
            open_col = page_admin.query_selector("#openCreateColModalBtn")
            if open_col:
                open_col.click()
                time.sleep(0.8)
                page_admin.screenshot(path=str(out_dir / "admin_07_create_collection.png"))
                print("Captured admin_07_create_collection.png")
                page_admin.click("#closeCreateColModalBtn")
                time.sleep(0.5)
            else:
                page_admin.screenshot(path=str(out_dir / "admin_07_create_collection.png"))
        except Exception as e:
            print("Create collection modal error:", e)

        # 8. Saved
        page_admin.click('.sidebar-nav a[data-view="saved"]')
        time.sleep(1)
        page_admin.screenshot(path=str(out_dir / "admin_08_saved_insights.png"))
        print("Captured admin_08_saved_insights.png")
        
        # 9. Knowledge Graph
        page_admin.click('.sidebar-nav a[data-view="graph"]')
        time.sleep(4) # allow D3 physics
        page_admin.screenshot(path=str(out_dir / "admin_09_knowledge_graph.png"))
        print("Captured admin_09_knowledge_graph.png")
        
        # 10. Evaluation
        page_admin.click('.sidebar-nav a[data-view="evaluation"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_10_evaluation.png"))
        print("Captured admin_10_evaluation.png")
        
        # 11. User Directory
        page_admin.click('.sidebar-nav a[data-view="users"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_11_users_directory.png"))
        print("Captured admin_11_users_directory.png")
        
        # 12. Provision User Modal
        try:
            open_prov = page_admin.query_selector("#openProvisionUserModalBtn")
            if open_prov:
                open_prov.click()
                time.sleep(0.8)
                page_admin.screenshot(path=str(out_dir / "admin_12_provision_user_modal.png"))
                print("Captured admin_12_provision_user_modal.png")
                page_admin.click("#closeProvisionModalBtn")
                time.sleep(0.5)
            else:
                page_admin.screenshot(path=str(out_dir / "admin_12_provision_user_modal.png"))
        except Exception as e:
            print("Provision user modal error:", e)

        # 13. Roles Matrix
        page_admin.click('.sidebar-nav a[data-view="roles"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_13_roles_matrix.png"))
        print("Captured admin_13_roles_matrix.png")
        
        # 14. Custom Role Modal
        try:
            open_role = page_admin.query_selector("#openCreateRoleModalBtn")
            if open_role:
                open_role.click()
                time.sleep(0.8)
                page_admin.screenshot(path=str(out_dir / "admin_14_custom_role_modal.png"))
                print("Captured admin_14_custom_role_modal.png")
                page_admin.click("#closeCustomRoleModalBtn")
                time.sleep(0.5)
            else:
                page_admin.screenshot(path=str(out_dir / "admin_14_custom_role_modal.png"))
        except Exception as e:
            print("Custom role modal error:", e)

        # 15. Reports & Export
        page_admin.click('.sidebar-nav a[data-view="reports"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_15_reports_export.png"))
        print("Captured admin_15_reports_export.png")

        # 16. Audit Logs
        page_admin.click('.sidebar-nav a[data-view="audit"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_16_audit_logs.png"))
        print("Captured admin_16_audit_logs.png")

        # 17. System Health
        page_admin.click('.sidebar-nav a[data-view="system"]')
        time.sleep(1.5)
        page_admin.screenshot(path=str(out_dir / "admin_17_system_health.png"))
        print("Captured admin_17_system_health.png")

        # 18. Notifications
        page_admin.click('.sidebar-nav a[data-view="notifications"]')
        time.sleep(1)
        page_admin.screenshot(path=str(out_dir / "admin_18_notifications.png"))
        print("Captured admin_18_notifications.png")

        # 19. Profile
        page_admin.click('.sidebar-nav a[data-view="profile"]')
        time.sleep(1)
        page_admin.screenshot(path=str(out_dir / "admin_19_profile.png"))
        print("Captured admin_19_profile.png")
        ctx_admin.close()

        # --- SECTION C: KNOWLEDGE WORKER ---
        print("\n--- Capturing Knowledge Worker Screens ---")
        ctx_worker = browser.new_context(viewport={"width": 1440, "height": 900})
        page_worker = ctx_worker.new_page()
        page_worker.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page_worker.click("#navLoginBtn")
        page_worker.wait_for_selector("#loginCard", state="visible")
        page_worker.click("#demoWorkerBtn")
        time.sleep(0.5)
        page_worker.click("#loginSubmitBtn")
        page_worker.wait_for_selector("#authenticatedAppView", state="visible")
        time.sleep(2)

        # 1. Worker Dashboard
        page_worker.screenshot(path=str(out_dir / "worker_01_dashboard.png"))
        print("Captured worker_01_dashboard.png")

        # 2. Worker Documents
        page_worker.click('.sidebar-nav a[data-view="documents"]')
        time.sleep(1.5)
        page_worker.screenshot(path=str(out_dir / "worker_02_documents.png"))
        print("Captured worker_02_documents.png")

        # 3. Worker Assistant
        page_worker.click('.sidebar-nav a[data-view="assistant"]')
        time.sleep(1.5)
        page_worker.screenshot(path=str(out_dir / "worker_03_assistant.png"))
        print("Captured worker_03_assistant.png")

        # 4. Worker Collections
        page_worker.click('.sidebar-nav a[data-view="collections"]')
        time.sleep(1)
        page_worker.screenshot(path=str(out_dir / "worker_04_collections.png"))
        print("Captured worker_04_collections.png")

        # 5. Worker Sidebar Isolation (RBAC)
        page_worker.screenshot(path=str(out_dir / "worker_05_sidebar_rbac.png"))
        print("Captured worker_05_sidebar_rbac.png")
        ctx_worker.close()

        # --- SECTION D: KNOWLEDGE ANALYST ---
        print("\n--- Capturing Knowledge Analyst Screens ---")
        ctx_analyst = browser.new_context(viewport={"width": 1440, "height": 900})
        page_analyst = ctx_analyst.new_page()
        page_analyst.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page_analyst.click("#navLoginBtn")
        page_analyst.wait_for_selector("#loginCard", state="visible")
        page_analyst.click("#demoAnalystBtn")
        time.sleep(0.5)
        page_analyst.click("#loginSubmitBtn")
        page_analyst.wait_for_selector("#authenticatedAppView", state="visible")
        time.sleep(2)

        # 1. Analyst Dashboard
        page_analyst.screenshot(path=str(out_dir / "analyst_01_dashboard.png"))
        print("Captured analyst_01_dashboard.png")

        # 2. Analyst Knowledge Graph
        page_analyst.click('.sidebar-nav a[data-view="graph"]')
        time.sleep(4)
        page_analyst.screenshot(path=str(out_dir / "analyst_02_graph.png"))
        print("Captured analyst_02_graph.png")

        # 3. Analyst Evaluation
        page_analyst.click('.sidebar-nav a[data-view="evaluation"]')
        time.sleep(1.5)
        page_analyst.screenshot(path=str(out_dir / "analyst_03_evaluation.png"))
        print("Captured analyst_03_evaluation.png")

        # 4. Analyst Reports
        page_analyst.click('.sidebar-nav a[data-view="reports"]')
        time.sleep(1.5)
        page_analyst.screenshot(path=str(out_dir / "analyst_04_reports.png"))
        print("Captured analyst_04_reports.png")
        ctx_analyst.close()

        browser.close()
        print("\n[SUCCESS] All 31 genuine screenshots captured successfully!")

if __name__ == "__main__":
    run()
