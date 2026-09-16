"""Bound model-safe projection for dynamic READ results."""

from __future__ import annotations

import json
from typing import Any


def bound_response_payload(
    data: Any,
    *,
    max_bytes: int,
    max_items: int,
) -> dict[str, Any]:
    """Return a bounded envelope; never raises on serialization issues."""
    truncated = False
    payload = data

    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list) and len(items) > max_items:
            payload = dict(payload)
            payload["items"] = items[:max_items]
            payload["is_complete"] = False
            payload["truncated"] = True
            truncated = True
        elif isinstance(items, list):
            payload = dict(payload)
            payload.setdefault("is_complete", True)
            payload.setdefault("truncated", False)

    try:
        raw = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError):
        return {
            "data": None,
            "truncated": True,
            "is_complete": False,
            "error": "RESPONSE_NOT_SERIALIZABLE",
        }

    if len(raw) > max_bytes:
        # Prefer truncating items again if present; else omit body.
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            keep = max(1, max_items // 2)
            while keep >= 1:
                slim = dict(payload)
                slim["items"] = payload["items"][:keep]
                slim["truncated"] = True
                slim["is_complete"] = False
                raw2 = json.dumps(slim, default=str, ensure_ascii=False).encode("utf-8")
                if len(raw2) <= max_bytes:
                    return {
                        "data": slim,
                        "truncated": True,
                        "is_complete": False,
                        "response_bytes": len(raw2),
                    }
                keep //= 2
        return {
            "data": None,
            "truncated": True,
            "is_complete": False,
            "error": "RESPONSE_TOO_LARGE",
            "response_bytes": len(raw),
        }

    return {
        "data": payload,
        "truncated": truncated,
        "is_complete": not truncated,
        "response_bytes": len(raw),
    }
