from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "device_api_messages.json"


@lru_cache(maxsize=1)
def load_device_api_messages() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def _section(name: str) -> dict[str, Any]:
    catalog = load_device_api_messages()
    section = catalog.get(name)
    if not isinstance(section, dict):
        return {}
    return section


def _device_connectivity_section() -> dict[str, Any]:
    return _section("deviceConnectivity")


def _http_errors_section() -> dict[str, Any]:
    return _section("httpErrors")


def _command_errors_section() -> dict[str, Any]:
    return _section("commandErrors")


def _validation_errors_section() -> dict[str, Any]:
    return _section("validationErrors")


def _format_message(template: str, params: dict[str, Any]) -> str:
    if not params:
        return template
    try:
        return template.format(**params)
    except KeyError:
        return template


def _lookup_message(section: dict[str, Any], code: str, *, fallback: str | None = None, **params: Any) -> str:
    messages = section.get("messages") if "messages" in section else section
    if isinstance(messages, dict):
        mapped = messages.get(code)
        if isinstance(mapped, str) and mapped.strip():
            return _format_message(mapped.strip(), params)
    if fallback and fallback.strip():
        return fallback.strip()
    default_message = section.get("fallbackMessage")
    if isinstance(default_message, str) and default_message.strip():
        return _format_message(default_message.strip(), params)
    return code


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


def device_connectivity_user_message(code: str, *, fallback: str | None = None, **params: Any) -> str:
    return _lookup_message(_device_connectivity_section(), code, fallback=fallback, **params)


def http_error_message(key: str, *, fallback: str | None = None, **params: Any) -> str:
    section = _http_errors_section()
    mapped = section.get(key)
    if isinstance(mapped, str) and mapped.strip():
        return _format_message(mapped.strip(), params)
    if fallback and fallback.strip():
        return fallback.strip()
    return key


def command_error_message(code: str, *, fallback: str | None = None, **params: Any) -> str:
    return _lookup_message(_command_errors_section(), code, fallback=fallback, **params)


def validation_error_message(code: str, *, fallback: str | None = None, **params: Any) -> str:
    return _lookup_message(_validation_errors_section(), code, fallback=fallback, **params)


__all__ = [
    "command_error_message",
    "device_connectivity_codes",
    "device_connectivity_http_status_code",
    "device_connectivity_user_message",
    "http_error_message",
    "load_device_api_messages",
    "validation_error_message",
]
