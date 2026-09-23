"""Catálogo declarativo do Alimentador de Linha (``content/line_feeder.json``)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "line_feeder.json"


@lru_cache(maxsize=1)
def line_feeder_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def setting_int(key: str, default: int) -> int:
    try:
        return int(line_feeder_settings().get(key, default))
    except (TypeError, ValueError):
        return default


def setting_str(key: str, default: str) -> str:
    value = str(line_feeder_settings().get(key) or "").strip()
    return value or default


def setting_map(key: str) -> dict[str, Any]:
    raw = line_feeder_settings().get(key)
    return raw if isinstance(raw, dict) else {}


def message(key: str, default: str) -> str:
    value = str(setting_map("messages").get(key) or "").strip()
    return value or default
