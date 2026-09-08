from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "content" / "firmware_ota_messages.json"
    return json.loads(path.read_text(encoding="utf-8"))


def firmware_ota_http_message(key: str, *, default: str | None = None) -> str:
    messages = _load().get("httpErrors") or {}
    value = messages.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return default or key


def reset_firmware_ota_messages_cache_for_tests() -> None:
    _load.cache_clear()
