# tests/conftest.py — deterministic environment for CORS-aware tests.
# Must run before app import: ALLOWED_ORIGINS is built at import time,
# so ambient runner values cannot influence the allowlist under test.
import os

import pytest

_CORS_ENV_KEYS = ("API_DELPI_ENV", "PUBLIC_BASE_URL", "VITE_KC_URL")
_saved_env = {key: os.environ.get(key) for key in _CORS_ENV_KEYS}

os.environ["API_DELPI_ENV"] = "development"
os.environ["PUBLIC_BASE_URL"] = "https://portal.example.com"
os.environ.pop("VITE_KC_URL", None)


@pytest.fixture(scope="session", autouse=True)
def _restore_cors_env():
    yield
    for key, value in _saved_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
