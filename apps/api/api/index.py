"""Vercel serverless entrypoint for the FastAPI backend.

Vercel's Python runtime serves the module-level `app` (an ASGI application).
The catch-all route in vercel.json forwards every path here with the original
URL preserved, so FastAPI's own `/api/...` routing matches as usual.
"""
import os
import sys

# Make the `app` package importable (project root = apps/api, this file = apps/api/api/index.py).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Serverless filesystem is read-only except /tmp. Use an ephemeral SQLite DB
# there; demo data is (re)seeded on cold start. Set before importing the app
# so config picks it up.
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/fitlens.db")
os.environ.setdefault("ENVIRONMENT", "production")

from app.main import app  # noqa: E402  -- ASGI app Vercel will serve
from app.seed import reset_and_seed  # noqa: E402

# The serverless ASGI adapter may not run lifespan startup events, so seed
# explicitly at cold start. Never block boot if seeding hiccups.
try:
    reset_and_seed()
except Exception:  # pragma: no cover - defensive
    pass
