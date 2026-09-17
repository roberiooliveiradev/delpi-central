"""Canonical chip LED operational states (GET /api/status ledState)."""

from __future__ import annotations

from typing import Any

KNOWN_LED_STATES = frozenset(
    {
        "offline",
        "connecting",
        "wifi_ok_never_contacted",
        "backend_ok",
        "wifi_ok_stale",
        "ota_in_progress",
        "auth_error",
    }
)


def normalize_led_state(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text not in KNOWN_LED_STATES:
        return None
    return text
