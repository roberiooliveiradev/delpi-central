"""Bound model-safe projection for dynamic READ results.

Size bounding ≠ field-level authorization.
Field projection is fail-closed from trusted governance metadata only.

Rule: DROP EVERYTHING → copy only approved fields (+ minimal technical pagination meta).
Never copy the original payload and prune.
IF IN DOUBT → DROP (never raw fallback).
"""

from __future__ import annotations

import json
import re
from typing import Any

# Strict path: identifiers + optional [] segments, joined by dots. No wildcards.
_VALID_PATH = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(\[\])?(\.[A-Za-z_][A-Za-z0-9_]*(\[\])?)*$"
)
_PATH_SEG = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(\[\])?")

# Minimal technical pagination / bound flags — not business data.
_TECHNICAL_META = frozenset(
    {
        "page",
        "page_size",
        "total",
        "total_pages",
        "is_complete",
        "truncated",
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


def _parse_path(path: str) -> list[tuple[str, bool]] | None:
    """Return list of (key, is_array) segments, or None if path is malformed."""
    text = (path or "").strip()
    if not text or not _VALID_PATH.fullmatch(text):
        return None
    segments: list[tuple[str, bool]] = []
    pos = 0
    while pos < len(text):
        if text[pos] == ".":
            pos += 1
            continue
        match = _PATH_SEG.match(text, pos)
        if not match:
            return None
        segments.append((match.group(1), match.group(2) == "[]"))
        pos = match.end()
    return segments or None


def _build_allow_tree(paths: list[str]) -> dict[str, Any]:
    """Tree: key → {"array": bool, "children": tree, "leaf": bool}."""
    root: dict[str, Any] = {}
    for path in paths:
        segs = _parse_path(path)
        if not segs:
            continue
        node = root
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
    truncated_flag: list[bool],
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
            if len(child) > max_array:
                truncated_flag[0] = True
            if children:
                projected_list = []
                for item in child[:max_array]:
                    projected = _project_with_tree(
                        item,
                        children,
                        depth=depth + 1,
                        max_depth=max_depth,
                        max_array=max_array,
                        truncated_flag=truncated_flag,
                    )
                    if projected is not None:
                        projected_list.append(projected)
                out[key] = projected_list
            elif spec.get("leaf"):
                # Leaf array without child schema: drop (cannot validate item shape).
                continue
            continue
        if children:
            projected = _project_with_tree(
                child,
                children,
                depth=depth + 1,
                max_depth=max_depth,
                max_array=max_array,
                truncated_flag=truncated_flag,
            )
            if projected is not None:
                out[key] = projected
        elif spec.get("leaf"):
            out[key] = child
    return out


def _copy_technical_meta(source: dict[str, Any], target: dict[str, Any]) -> None:
    for meta_key in _TECHNICAL_META:
        if meta_key in source and meta_key not in target:
            target[meta_key] = source[meta_key]


def apply_approved_field_projection(
    data: Any,
    *,
    approved_fields: tuple[str, ...] | list[str] | None,
    list_key: str = "items",
    max_depth: int = 8,
    max_array_items: int = 50,
) -> Any:
    """Build a new payload with only approved fields. Never preserve originals."""
    if not approved_fields:
        return {}

    payload = unwrap_api_payload(data)
    fields = [str(f) for f in approved_fields if f]
    if not fields:
        return {}

    if _uses_path_syntax(fields):
        if not isinstance(payload, dict):
            return {}
        tree = _build_allow_tree(fields)
        if not tree:
            return {}
        truncated_flag = [False]
        projected = _project_with_tree(
            payload,
            tree,
            depth=0,
            max_depth=max_depth,
            max_array=max_array_items,
            truncated_flag=truncated_flag,
        )
        if not isinstance(projected, dict):
            return {}
        _copy_technical_meta(payload, projected)
        if truncated_flag[0]:
            projected["truncated"] = True
            projected["is_complete"] = False
        return projected

    # Flat mode — construct from scratch.
    if isinstance(payload, list):
        out_list: list[Any] = []
        for item in payload[:max_array_items]:
            if not isinstance(item, dict):
                continue
            out_list.append({k: item[k] for k in fields if k in item})
        return out_list

    if not isinstance(payload, dict):
        return {}

    out: dict[str, Any] = {}
    items = payload.get(list_key)
    if isinstance(items, list):
        projected_items: list[Any] = []
        truncated = len(items) > max_array_items
        for item in items[:max_array_items]:
            if isinstance(item, dict):
                projected_items.append({k: item[k] for k in fields if k in item})
        out[list_key] = projected_items
        _copy_technical_meta(payload, out)
        if truncated:
            out["truncated"] = True
            out["is_complete"] = False
        return out

    # Flat root object.
    for key in fields:
        if key in payload:
            out[key] = payload[key]
    _copy_technical_meta(payload, out)
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
        if payload.get("truncated") is True:
            truncated = True
            payload = dict(payload)
            payload["is_complete"] = False
            payload["truncated"] = True
    elif isinstance(payload, list) and len(payload) > max_items:
        payload = payload[:max_items]
        truncated = True

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
