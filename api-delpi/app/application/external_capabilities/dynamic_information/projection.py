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


def _as_non_negative_int(value: Any) -> int | None:
    """Parse pagination scalars; reject bools and negatives as untrustworthy."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer():
        as_int = int(value)
        return as_int if as_int >= 0 else None
    return None


def source_pagination_proves_partial(payload: dict[str, Any]) -> bool | None:
    """Interpret canonical page/page_size/total/total_pages for dataset completeness.

    Returns:
      True  — metadata proves the payload is only a partial dataset
      False — metadata proves the payload covers the full query scope
      None  — pagination metadata absent, untrustworthy, or insufficient
    """
    has_pagination_keys = any(
        key in payload for key in ("page", "page_size", "total", "total_pages")
    )
    if not has_pagination_keys:
        return None

    raw_page = payload.get("page") if "page" in payload else None
    raw_page_size = payload.get("page_size") if "page_size" in payload else None
    raw_total = payload.get("total") if "total" in payload else None
    raw_total_pages = payload.get("total_pages") if "total_pages" in payload else None

    # Malformed present values → do not invent completeness.
    if "page" in payload:
        page = _as_non_negative_int(raw_page)
        if page is None or page < 1:
            return None
    else:
        page = None
    if "page_size" in payload:
        page_size = _as_non_negative_int(raw_page_size)
        if page_size is None:
            return None
    else:
        page_size = None
    if "total" in payload:
        total = _as_non_negative_int(raw_total)
        if total is None:
            return None
    else:
        total = None
    if "total_pages" in payload:
        total_pages = _as_non_negative_int(raw_total_pages)
        if total_pages is None:
            return None
    else:
        total_pages = None

    items = payload.get("items")
    visible = len(items) if isinstance(items, list) else None

    # Multi-page datasets are always partial for a single returned page —
    # including the last page (page == total_pages).
    if total_pages is not None and total_pages > 1:
        return True
    if total is not None and visible is not None and total > visible:
        return True

    # Empty or single-page scopes that fit the visible rows.
    if total is not None and visible is not None and total <= visible:
        if total_pages is None or total_pages <= 1:
            return False
    if total_pages is not None and total_pages <= 1:
        if total is None or visible is None or total <= visible:
            return False

    # page/page_size alone without total/total_pages cannot prove completeness.
    _ = (page, page_size)
    return None


def derive_response_completeness(
    payload: Any,
    *,
    davi_item_truncated: bool = False,
    davi_byte_truncated: bool = False,
) -> tuple[bool, bool]:
    """Derive (is_complete, truncated) for the model-visible broker response.

    is_complete = model-visible payload contains the full result set for the
    current canonical query scope.
    truncated = model-visible payload is only a bounded/partial subset.

    Precedence is monotonic/conservative: proven incompleteness never becomes
    complete later. Source ``is_complete=false`` / ``truncated=true`` are sticky.
    Source optimistic True may be overridden by pagination or DAVI bounding.
    """
    is_complete = True
    truncated = False

    if isinstance(payload, dict):
        if payload.get("truncated") is True:
            truncated = True
            is_complete = False
        if payload.get("is_complete") is False:
            is_complete = False
            truncated = True

        pagination_partial = source_pagination_proves_partial(payload)
        if pagination_partial is True:
            is_complete = False
            truncated = True

    if davi_item_truncated or davi_byte_truncated:
        is_complete = False
        truncated = True

    if truncated:
        is_complete = False
    return is_complete, truncated


def bound_response_payload(
    data: Any,
    *,
    max_bytes: int,
    max_items: int,
) -> dict[str, Any]:
    """Return a size-bounded envelope (does not authorize fields)."""
    davi_item_truncated = False
    payload: Any = data

    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list) and len(items) > max_items:
            payload = dict(payload)
            payload["items"] = items[:max_items]
            davi_item_truncated = True
        elif isinstance(items, list):
            payload = dict(payload)
    elif isinstance(payload, list) and len(payload) > max_items:
        payload = payload[:max_items]
        davi_item_truncated = True

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
                is_complete, truncated = derive_response_completeness(
                    slim,
                    davi_item_truncated=True,
                    davi_byte_truncated=True,
                )
                slim["is_complete"] = is_complete
                slim["truncated"] = truncated
                raw2 = json.dumps(slim, default=str, ensure_ascii=False).encode("utf-8")
                if len(raw2) <= max_bytes:
                    return {
                        "data": slim,
                        "truncated": truncated,
                        "is_complete": is_complete,
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

    is_complete, truncated = derive_response_completeness(
        payload if isinstance(payload, dict) else {},
        davi_item_truncated=davi_item_truncated,
        davi_byte_truncated=False,
    )
    if isinstance(payload, list) and davi_item_truncated:
        is_complete, truncated = False, True
    if isinstance(payload, dict) and (
        isinstance(payload.get("items"), list)
        or "is_complete" in payload
        or "truncated" in payload
        or truncated
        or not is_complete
    ):
        payload = dict(payload)
        payload["is_complete"] = is_complete
        payload["truncated"] = truncated

    return {
        "data": payload,
        "truncated": truncated,
        "is_complete": is_complete,
        "response_bytes": len(raw),
    }
