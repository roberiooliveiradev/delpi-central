"""Load governance content for DAVI dynamic READ."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_ROOT = Path(__file__).resolve().parents[3] / "content"


@lru_cache(maxsize=1)
def load_external_read_allowlist() -> dict[str, Any]:
    path = _CONTENT_ROOT / "davi_external_read_allowlist.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_dynamic_read_budgets() -> dict[str, Any]:
    path = _CONTENT_ROOT / "davi_dynamic_read_budgets.json"
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_token_secret() -> str:
    from app.config import settings

    # Prefer dedicated secret when present; fall back to JWT_SECRET for HMAC integrity.
    dedicated = getattr(settings, "DAVI_CANDIDATE_HMAC_SECRET", None)
    if dedicated:
        return str(dedicated)
    return str(settings.JWT_SECRET or "")
