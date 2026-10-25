import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("enterprise-knowledge-navigator/frontend/index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re

m = re.search(r'id=["\']view-search["\']', text)
if m:
    print("=== view-search content ===")
    print(text[m.start():m.start() + 2000])

m2 = re.search(r'id=["\']view-assistant["\']', text)
if m2:
    print("=== view-assistant content ===")
    print(text[m2.start():m2.start() + 2000])





