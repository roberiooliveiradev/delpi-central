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
    """Resolve HMAC secret for candidate tokens.

    Precedence:
      1. ``DAVI_CANDIDATE_HMAC_SECRET`` (dedicated, preferred for production)
      2. ``JWT_SECRET`` (compatibility fallback only)

    Never log the returned value.
    """
    from app.config import settings

    dedicated = (settings.DAVI_CANDIDATE_HMAC_SECRET or "").strip()
    if dedicated:
        return dedicated
    return str(settings.JWT_SECRET or "")
