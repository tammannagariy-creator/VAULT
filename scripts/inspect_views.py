import re

with open(r"C:\surya\vault\dashboard\public\index.html", "r", encoding="utf-8") as f:
    text = f.read()

views = re.findall(r"(\w+):\s*\{\s*section:\s*['\"]([^'\"]+)['\"]\s*,\s*title:\s*['\"]([^'\"]+)['\"]", text)
print(f"Current views count: {len(views)}")
for v in views:
    print(f"{v[0]:20} | {v[1]:15} | {v[2]}")
