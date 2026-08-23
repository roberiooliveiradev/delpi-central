"""Catálogo declarativo de Materiais (``content/materials.json``)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "materials.json"


@lru_cache(maxsize=1)
def materials_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def setting_int(key: str, default: int) -> int:
    try:
        return int(materials_settings().get(key, default))
    except (TypeError, ValueError):
        return default


def setting_list(key: str) -> tuple[str, ...]:
    raw = materials_settings().get(key)
    if not isinstance(raw, list):
        return ()
    return tuple(str(item).strip() for item in raw if str(item).strip())


def setting_str(key: str, default: str) -> str:
    value = str(materials_settings().get(key) or "").strip()
    return value or default


def setting_map(key: str) -> dict[str, Any]:
    raw = materials_settings().get(key)
    return raw if isinstance(raw, dict) else {}
