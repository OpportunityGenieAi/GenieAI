"""Adds the articles feature to app/main.py (safe to run twice)."""
from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")
if "articles.router" in s:
    raise SystemExit("Already applied")
a = "from app.routers import notifications\n"
b = "app.include_router(notifications.router)\n"
if a not in s or b not in s:
    raise SystemExit("main.py is different from expected - send me app/main.py")
s = s.replace(a, a + "from app.routers import articles\nfrom app import article_model  # noqa: F401  (registers the articles table)\n", 1)
s = s.replace(b, b + "app.include_router(articles.router)\n", 1)
p.write_text(s, encoding="utf-8")
print("Applied")
