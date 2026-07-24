"""Helpers canônicos para smoke Nível A (envelope {success, message, data})."""

from __future__ import annotations

import json
from typing import Any


def body_json(response: Any) -> dict[str, Any]:
    raw = getattr(response, "body", None)
    if raw is not None and not hasattr(response, "json"):
        return json.loads(raw.decode())
    return response.json()


def assert_ok_envelope(body: dict[str, Any], *, allow_null_data: bool = True) -> None:
    assert body.get("success") is True, body
    assert "message" in body, body
    if not allow_null_data:
        assert body.get("data") is not None, body


def assert_plain_health(body: dict[str, Any]) -> None:
    assert body.get("status") in {"online", "degraded"}, body
