"""
Scratch audit script to verify frontend element IDs, API route bindings,
and edge case coverage across document processing and retrieval.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.main import app

def audit_frontend():
    html_path = Path("frontend/index.html")
    js_path = Path("frontend/app.js")
    css_path = Path("frontend/style.css")

    html = html_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")

    # Match getElementById
    js_ids = set(re.findall(r'document\.getElementById\(["\']([^"\']+)["\']\)', js))
    # Match querySelector with #
    js_query_ids = set(re.findall(r'querySelector\(["\']#([^"\', >]+)["\']\)', js))
    all_js_ids = js_ids | js_query_ids

    # Match IDs in HTML
    html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))

    missing = all_js_ids - html_ids
    print(f"Total IDs referenced in JS: {len(all_js_ids)}")
    print(f"Total IDs present in HTML: {len(html_ids)}")
    print(f"Missing in HTML: {sorted(list(missing))}")

    # Check button onclicks and data attributes
    buttons_in_html = re.findall(r'<button[^>]*>', html)
    print(f"Total buttons in HTML: {len(buttons_in_html)}")

    # Check API endpoints called in JS
    api_calls = set(re.findall(r'fetch\(["\`](/[^"\`?]+)["\`?]', js))
    print(f"\nTotal unique API paths called in JS: {len(api_calls)}")
    for c in sorted(api_calls):
        print(f"  - {c}")

    # Inspect all registered routes in FastAPI
    print("\n--- Registered FastAPI Routes ---")
    registered_routes = []
    for r in app.routes:
        methods = getattr(r, "methods", None)
        path = getattr(r, "path", None)
        if path:
            m_str = ",".join(sorted(methods)) if methods else "MOUNT"
            registered_routes.append(f"{m_str} {path}")

    print(f"Total registered FastAPI routes: {len(registered_routes)}")
    for r in sorted(registered_routes):
        print(f"  {r}")

if __name__ == "__main__":
    audit_frontend()
