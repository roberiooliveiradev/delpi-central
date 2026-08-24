"""Catálogo declarativo do mapa de entrega (``content/delivery_map.json``)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "delivery_map.json"


@lru_cache(maxsize=1)
def delivery_map_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def delivery_map_setting_int(key: str, default: int) -> int:
    try:
        return int(delivery_map_settings().get(key, default))
    except (TypeError, ValueError):
        return default


def delivery_map_setting_str(key: str, default: str = "") -> str:
    value = str(delivery_map_settings().get(key) or "").strip()
    return value or default


def delivery_map_product_prefixes() -> list[str]:
    raw = delivery_map_settings().get("productCodePrefixes")
    if not isinstance(raw, list):
        return ["8", "9"]
    return [str(item).strip() for item in raw if str(item).strip()]


def delivery_map_message(key: str, default: str) -> str:
    messages = delivery_map_settings().get("drawingMessages")
    if not isinstance(messages, dict):
        return default
    value = str(messages.get(key) or "").strip()
    return value or default
