"""Bound model-safe projection for dynamic READ results.

IMPORTANT:
  ``bound_response_payload`` only enforces size/item budgets.
  Size bounding ≠ field-level authorization / approved projection.

An operation may enter the DAVI allowlist only when its canonical HTTP response
is itself approved for external processing OR an approved explicit projection
exists (see ``apply_approved_field_projection`` / allowlist approvedResponseFields).
"""

from __future__ import annotations

import json
from typing import Any


def apply_approved_field_projection(
    data: Any,
    *,
    approved_fields: tuple[str, ...] | list[str] | None,
    list_key: str = "items",
) -> Any:
    """Keep only approved fields on list items when an allowlist is configured.

    If ``approved_fields`` is empty/None, returns data unchanged (caller must not
    treat size bounding as field authorization — those ops must not be allowlisted
    without an independent projection decision).
    """
    if not approved_fields:
        return data
    allowed = set(approved_fields)
    if not isinstance(data, dict):
        return data
    out = dict(data)
    items = out.get(list_key)
    if isinstance(items, list):
        projected_items: list[Any] = []
        for item in items:
            if isinstance(item, dict):
                projected_items.append({k: item.get(k) for k in approved_fields if k in allowed})
            else:
                projected_items.append(item)
        out[list_key] = projected_items
    return out


def bound_response_payload(
    data: Any,
    *,
    max_bytes: int,
    max_items: int,
) -> dict[str, Any]:
    """Return a size-bounded envelope.

    Does NOT authorize fields. Use ``apply_approved_field_projection`` first when
    the operation has an approved field allowlist.
    """
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
