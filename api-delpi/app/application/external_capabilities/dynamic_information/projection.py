"""Bound model-safe projection for dynamic READ results.

Size bounding ≠ field-level authorization.
Field projection is fail-closed from trusted governance metadata only.
Supports flat ``items[]`` keys and dotted/``[]`` nested paths.
"""

from __future__ import annotations

import json
import re
from typing import Any

_PATH_SEG = re.compile(r"([^.\[]+)(\[\])?")
_ENVELOPE_KEYS = frozenset({"success", "message", "error", "meta", "data"})
_PAGINATION_META = frozenset(
    {
        "page",
        "page_size",
        "total",
        "total_pages",
        "is_complete",
        "truncated",
        "bom_validity",
        "reference_date",
        "start_date",
        "date_end_exclusive",
    }
)


def unwrap_api_payload(data: Any) -> Any:
    """Prefer API DELPI ``data`` body when a success envelope is present."""
    if not isinstance(data, dict):
        return data
    if "data" in data and any(k in data for k in ("success", "meta", "message", "error")):
        return data.get("data")
    return data


def _uses_path_syntax(fields: tuple[str, ...] | list[str]) -> bool:
    return any(("." in f) or ("[]" in f) for f in fields)


def _parse_path(path: str) -> list[tuple[str, bool]]:
    """Return list of (key, is_array) segments."""
    segments: list[tuple[str, bool]] = []
    pos = 0
    text = path.strip()
    while pos < len(text):
        if text[pos] == ".":
            pos += 1
            continue
        match = _PATH_SEG.match(text, pos)
        if not match:
            break
        key, arr = match.group(1), match.group(2) == "[]"
        segments.append((key, arr))
        pos = match.end()
    return segments


def _build_allow_tree(paths: list[str]) -> dict[str, Any]:
    """Tree: key → {"array": bool, "children": tree|None, "leaf": bool}."""
    root: dict[str, Any] = {}
    for path in paths:
        node = root
        segs = _parse_path(path)
        if not segs:
            continue
        for idx, (key, is_array) in enumerate(segs):
            leaf = idx == len(segs) - 1
            entry = node.setdefault(key, {"array": is_array, "children": {}, "leaf": False})
            entry["array"] = entry["array"] or is_array
            if leaf:
                entry["leaf"] = True
            else:
                node = entry["children"]
    return root


def _project_with_tree(
    value: Any,
    tree: dict[str, Any],
    *,
    depth: int,
    max_depth: int,
    max_array: int,
) -> Any:
    if depth > max_depth:
        return None
    if not isinstance(value, dict):
        return None
    out: dict[str, Any] = {}
    for key, spec in tree.items():
        if key not in value:
            continue
        child = value.get(key)
        children = spec.get("children") or {}
        is_array = bool(spec.get("array"))
        if is_array:
            if not isinstance(child, list):
                continue
            if children:
                projected_list = []
                for item in child[:max_array]:
                    projected = _project_with_tree(
                        item,
                        children,
                        depth=depth + 1,
                        max_depth=max_depth,
                        max_array=max_array,
                    )
                    if projected is not None:
                        projected_list.append(projected)
                out[key] = projected_list
            elif spec.get("leaf"):
                out[key] = child[:max_array]
            continue
        if children:
            projected = _project_with_tree(
                child,
                children,
                depth=depth + 1,
                max_depth=max_depth,
                max_array=max_array,
            )
            if projected is not None:
                out[key] = projected
        elif spec.get("leaf"):
            out[key] = child
    return out


def apply_approved_field_projection(
    data: Any,
    *,
    approved_fields: tuple[str, ...] | list[str] | None,
    list_key: str = "items",
    max_depth: int = 8,
    max_array_items: int = 50,
) -> Any:
    """Keep only approved fields. Fail-closed for unknown keys/objects."""
    if not approved_fields:
        return data

    payload = unwrap_api_payload(data)
    fields = [str(f) for f in approved_fields if f]

    if _uses_path_syntax(fields):
        tree = _build_allow_tree(fields)
        projected = _project_with_tree(
            payload if isinstance(payload, dict) else {},
            tree,
            depth=0,
            max_depth=max_depth,
            max_array=max_array_items,
        )
        if not isinstance(projected, dict):
            return {}
        # Preserve harmless pagination/meta scalars when present and not already projected.
        if isinstance(payload, dict):
            for meta_key in _PAGINATION_META:
                if meta_key in payload and meta_key not in projected:
                    projected[meta_key] = payload[meta_key]
        return projected

    allowed = set(fields)
    if not isinstance(payload, dict):
        return payload
    out = dict(payload)
    items = out.get(list_key)
    if isinstance(items, list):
        projected_items: list[Any] = []
        for item in items:
            if isinstance(item, dict):
                projected_items.append({k: item.get(k) for k in fields if k in allowed})
            else:
                projected_items.append(item)
        out[list_key] = projected_items
        # Drop non-approved sibling object bags when projecting flat list payloads.
        for key in list(out.keys()):
            if key == list_key or key in _PAGINATION_META:
                continue
            if key in _ENVELOPE_KEYS:
                out.pop(key, None)
    return out


def bound_response_payload(
    data: Any,
    *,
    max_bytes: int,
    max_items: int,
) -> dict[str, Any]:
    """Return a size-bounded envelope (does not authorize fields)."""
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
