from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "device_api_messages.json"


@lru_cache(maxsize=1)
def load_device_api_messages() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def _device_connectivity_section() -> dict[str, Any]:
    catalog = load_device_api_messages()
    section = catalog.get("deviceConnectivity")
    if not isinstance(section, dict):
        return {}
    return section


@lru_cache(maxsize=1)
def device_connectivity_codes() -> frozenset[str]:
    section = _device_connectivity_section()
    codes = section.get("codes")
    if not isinstance(codes, list):
        return frozenset()
    return frozenset(str(code) for code in codes if str(code).strip())


def device_connectivity_http_status_code(*, default: int = 422) -> int:
    section = _device_connectivity_section()
    status_code = section.get("httpStatusCode")
    if isinstance(status_code, int) and 400 <= status_code <= 499:
        return status_code
    return default


def device_connectivity_user_message(code: str, *, fallback: str | None = None) -> str:
    section = _device_connectivity_section()
    messages = section.get("messages")
    if isinstance(messages, dict):
        mapped = messages.get(code)
        if isinstance(mapped, str) and mapped.strip():
            return mapped.strip()
    if fallback and fallback.strip():
        return fallback.strip()
    default_message = section.get("fallbackMessage")
    if isinstance(default_message, str) and default_message.strip():
        return default_message.strip()
    return "O dispositivo não respondeu à leitura."


__all__ = [
    "device_connectivity_codes",
    "device_connectivity_http_status_code",
    "device_connectivity_user_message",
    "load_device_api_messages",
]
