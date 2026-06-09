"""Definições versionadas das smoke suites do console API DELPI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "smoke_definitions.json"


@lru_cache(maxsize=1)
def load_smoke_definitions() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload.get("suites"), list):
        raise ValueError("smoke_definitions.json deve conter a chave 'suites' (lista).")
    return payload
