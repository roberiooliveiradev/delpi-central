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


_PAGINATION_KEYS = ("page", "page_size", "total", "total_pages")

# Internal pagination completeness states (not a public response field).
_PAGINATION_ABSENT = "absent"
_PAGINATION_COMPLETE = "complete"
_PAGINATION_PARTIAL = "partial"
_PAGINATION_UNKNOWN = "unknown"


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


def _pagination_view(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize top-level or nested ``pagination`` scalars for classification.

    Generic contract support for APIs that nest page/page_size/total under
    ``pagination`` (e.g. commercial OTD rankings). Prefer explicit top-level
    keys when present. Nested ``has_more: true`` proves partiality.
    """
    view = dict(payload)
    nested = payload.get("pagination")
    if isinstance(nested, dict):
        for key in _PAGINATION_KEYS:
            if key not in view and key in nested:
                view[key] = nested[key]
        if "has_more" not in view and "has_more" in nested:
            view["has_more"] = nested["has_more"]
    return view


def classify_source_pagination(payload: dict[str, Any]) -> str:
    """Classify canonical page/page_size/total/total_pages for dataset completeness.

    Returns one of:
      absent   — no pagination keys present
      complete — metadata proves full query-scope coverage
      partial  — metadata proves the payload is only a subset
      unknown  — pagination keys present but untrustworthy/insufficient
    """
    surface = _pagination_view(payload)
    present = [key for key in _PAGINATION_KEYS if key in surface]
    if not present:
        if surface.get("has_more") is True:
            return _PAGINATION_PARTIAL
        return _PAGINATION_ABSENT

    if surface.get("has_more") is True:
        return _PAGINATION_PARTIAL

    parsed: dict[str, int | None] = {}
    for key in _PAGINATION_KEYS:
        if key not in surface:
            parsed[key] = None
            continue
        value = _as_non_negative_int(surface.get(key))
        if value is None:
            return _PAGINATION_UNKNOWN
        if key in ("page", "page_size") and value < 1:
            return _PAGINATION_UNKNOWN
        parsed[key] = value

    page = parsed["page"]
    page_size = parsed["page_size"]
    total = parsed["total"]
    total_pages = parsed["total_pages"]

    items = payload.get("items")
    visible = len(items) if isinstance(items, list) else None
    # Internally contradictory combinations cannot prove completeness.
    if page is not None and total_pages is not None:
        if total_pages >= 1 and page > total_pages:
            return _PAGINATION_UNKNOWN
        if total_pages == 0 and page > 1:
            return _PAGINATION_UNKNOWN
    if total is not None and total_pages is not None:
        if total_pages == 0 and total > 0:
            return _PAGINATION_UNKNOWN
        if total_pages > 1 and total == 0:
            return _PAGINATION_UNKNOWN
    if total is not None and visible is not None and total < visible:
        return _PAGINATION_UNKNOWN
    if (
        total is not None
        and visible is not None
        and total_pages is not None
        and total_pages > 1
        and total == visible
    ):
        # Claims multi-page scope but this page already holds the full total.
        return _PAGINATION_UNKNOWN

    # Proven partiality — including last page of a multi-page dataset.
    if total_pages is not None and total_pages > 1:
        return _PAGINATION_PARTIAL
    if total is not None and visible is not None and total > visible:
        return _PAGINATION_PARTIAL

    # Proven completeness: empty or single-page scopes that fit visible rows.
    if total is not None and visible is not None and total <= visible:
        if total_pages is None or total_pages <= 1:
            return _PAGINATION_COMPLETE
    if total_pages is not None and total_pages <= 1:
        if total is not None and (visible is None or total <= visible):
            return _PAGINATION_COMPLETE
        if total is None and visible is not None:
            # total_pages alone without total is insufficient proof.
            return _PAGINATION_UNKNOWN

    # page/page_size (and other insufficient combinations) present but unproven.
    _ = page_size
    return _PAGINATION_UNKNOWN


def source_pagination_proves_partial(payload: dict[str, Any]) -> bool | None:
    """Backward-compatible view of :func:`classify_source_pagination`.

    True/False only for proven partial/complete. Absent and unknown both map to
    None — callers that need the absent/unknown distinction must use
    ``classify_source_pagination``.
    """
    state = classify_source_pagination(payload)
    if state == _PAGINATION_PARTIAL:
        return True
    if state == _PAGINATION_COMPLETE:
        return False
    return None


def derive_response_completeness(
    payload: Any,
    *,
    davi_item_truncated: bool = False,
    davi_byte_truncated: bool = False,
) -> tuple[bool, bool]:
    """Derive (is_complete, truncated) for the model-visible broker response.

    Public boolean mapping of internal pagination states:
      COMPLETE → (True, False)
      PARTIAL  → (False, True)
      UNKNOWN  → (False, False)
      ABSENT   → legacy default (True, False) unless other signals apply

    Precedence (monotonic):
      DAVI bound partial > source explicit partial > pagination PARTIAL
      > pagination UNKNOWN > pagination COMPLETE / legacy absent
    """
    pagination_state = _PAGINATION_ABSENT
    source_explicit_partial = False

    if isinstance(payload, dict):
        if payload.get("truncated") is True or payload.get("is_complete") is False:
            source_explicit_partial = True
        pagination_state = classify_source_pagination(payload)

    if davi_item_truncated or davi_byte_truncated:
        return False, True
    if source_explicit_partial:
        return False, True
    if pagination_state == _PAGINATION_PARTIAL:
        return False, True
    if pagination_state == _PAGINATION_UNKNOWN:
        return False, False
    # ABSENT (legacy) or COMPLETE
    return True, False


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
