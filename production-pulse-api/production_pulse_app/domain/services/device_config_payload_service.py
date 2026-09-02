from __future__ import annotations

from typing import Any


def build_configure_http_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Build EN body for POST /api/config. Omits write-only secrets when empty."""
    if not isinstance(payload, dict):
        return {}

    body: dict[str, Any] = {}

    if "ssid" in payload or "wifiSsid" in payload:
        ssid = payload.get("ssid") if "ssid" in payload else payload.get("wifiSsid")
        if ssid is not None and str(ssid).strip():
            body["ssid"] = str(ssid).strip()

    if "password" in payload or "wifiPassword" in payload:
        password = payload.get("password") if "password" in payload else payload.get("wifiPassword")
        if password is not None and str(password) != "":
            body["password"] = str(password)

    if "apiToken" in payload:
        token = payload.get("apiToken")
        if token is not None:
            body["apiToken"] = str(token).strip()

    if "debounceMs" in payload:
        try:
            body["debounceMs"] = int(payload.get("debounceMs"))
        except (TypeError, ValueError):
            pass

    return body


__all__ = ["build_configure_http_payload"]
