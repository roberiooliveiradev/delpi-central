from __future__ import annotations

from typing import Any

from production_pulse_app.core.serialize import json_safe


def success(data: Any = None, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"success": True, "data": json_safe(data)}
    if meta is not None:
        payload["meta"] = json_safe(meta)
    return payload


def error(
    message: str,
    *,
    code: str = "error",
    status_code: int = 400,
    details: Any = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        payload["error"]["details"] = json_safe(details)
    payload["_status_code"] = status_code
    return payload
