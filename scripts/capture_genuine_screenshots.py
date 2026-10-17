"""
Captures genuine, high-resolution screenshots of the actual running application.
Saves screenshots to docs/screenshots/.
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def capture_all():
    screenshot_dir = Path("docs/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        # 1. Landing Page
        print("Capturing 01_landing_page.png...")
        ctx1 = browser.new_context(viewport={"width": 1366, "height": 820})
        page1 = ctx1.new_page()
        page1.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        time.sleep(1.5)
        page1.screenshot(path=str(screenshot_dir / "01_landing_page.png"))
        ctx1.close()
        
        # 2. Login Portal
        print("Capturing 02_login_portal.png...")
        ctx2 = browser.new_context(viewport={"width": 1366, "height": 820})
        page2 = ctx2.new_page()
        page2.goto("http://127.0.0.1:8000/")
        page2.wait_for_timeout(1000)
        page2.click("#navLoginBtn")
        page2.wait_for_timeout(1000)
        page2.screenshot(path=str(screenshot_dir / "02_login_portal.png"))
        ctx2.close()
        
        # 3. Knowledge Worker Dashboard
        print("Capturing 03_worker_dashboard.png...")
        ctx3 = browser.new_context(viewport={"width": 1366, "height": 820})
        page3 = ctx3.new_page()
        page3.goto("http://127.0.0.1:8000/")
        page3.wait_for_timeout(1000)
        page3.click("#navLoginBtn")
        page3.wait_for_timeout(500)
        page3.click("#demoWorkerBtn")
        page3.wait_for_timeout(500)
        page3.click("#loginSubmitBtn")
        page3.wait_for_selector("#authenticatedAppView", state="visible")
        page3.wait_for_timeout(2000)
        page3.screenshot(path=str(screenshot_dir / "03_worker_dashboard.png"))
        ctx3.close()
        
        # 4. Grounded Q&A Assistant View
        print("Capturing 04_grounded_assistant.png...")
        ctx4 = browser.new_context(viewport={"width": 1366, "height": 820})
        page4 = ctx4.new_page()
        page4.goto("http://127.0.0.1:8000/")
        page4.wait_for_timeout(1000)
        page4.click("#navLoginBtn")
        page4.wait_for_timeout(500)
        page4.click("#demoWorkerBtn")
        page4.wait_for_timeout(500)
        page4.click("#loginSubmitBtn")
        page4.wait_for_selector("#authenticatedAppView", state="visible")
        page4.wait_for_timeout(1500)
        page4.click('.sidebar-nav a[data-view="assistant"]')
        page4.wait_for_timeout(2000)
        page4.screenshot(path=str(screenshot_dir / "04_grounded_assistant.png"))
        ctx4.close()
        
        # 5. Analyst Knowledge Graph View
        print("Capturing 05_knowledge_graph.png...")
        ctx5 = browser.new_context(viewport={"width": 1366, "height": 820})
        page5 = ctx5.new_page()
        page5.goto("http://127.0.0.1:8000/")
        page5.wait_for_timeout(1000)
        page5.click("#navLoginBtn")
        page5.wait_for_timeout(500)
        page5.click("#demoAnalystBtn")
        page5.wait_for_timeout(500)
        page5.click("#loginSubmitBtn")
        page5.wait_for_selector("#authenticatedAppView", state="visible")
        page5.wait_for_timeout(1500)
        page5.click('.sidebar-nav a[data-view="graph"]')
        # Wait for D3 force layout simulation to stabilize
        page5.wait_for_timeout(4000)
        page5.screenshot(path=str(screenshot_dir / "05_knowledge_graph.png"))
        ctx5.close()
        
        # 6. Admin Roles & Permissions Matrix
        print("Capturing 06_admin_portal.png...")
        ctx6 = browser.new_context(viewport={"width": 1366, "height": 820})
        page6 = ctx6.new_page()
        page6.goto("http://127.0.0.1:8000/")
        page6.wait_for_timeout(1000)
        page6.click("#navLoginBtn")
        page6.wait_for_timeout(500)
        page6.click("#demoAdminBtn")
        page6.wait_for_timeout(500)
        page6.click("#loginSubmitBtn")
        page6.wait_for_selector("#authenticatedAppView", state="visible")
        page6.wait_for_timeout(1500)
        page6.click('.sidebar-nav a[data-view="roles"]')
        page6.wait_for_timeout(2000)
        page6.screenshot(path=str(screenshot_dir / "06_admin_portal.png"))
        ctx6.close()
        
        browser.close()
        print("SUCCESS: All 6 application screenshots captured into docs/screenshots/!")

if __name__ == "__main__":
    capture_all()
