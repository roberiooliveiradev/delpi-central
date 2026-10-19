# tests/conftest.py — controls the environment for CORS-aware tests.
# Must run before app import: ALLOWED_ORIGINS is built at import time.
import os

os.environ.setdefault("API_DELPI_ENV", "development")
os.environ.setdefault("PUBLIC_BASE_URL", "https://portal.example.com")
