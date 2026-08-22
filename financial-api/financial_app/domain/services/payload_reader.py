from __future__ import annotations

from typing import Any


def unwrap_data(payload: Any) -> dict[str, Any]:
    """Extrai o ``data`` do envelope da api-delpi, tolerando payload já cru."""
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


def unwrap_items(payload: Any, key: str = "items") -> list[dict[str, Any]]:
    source = unwrap_data(payload)
    items = source.get(key)
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def as_optional_text(value: Any) -> str | None:
    text = as_text(value)
    return text or None


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def as_number(value: Any, default: float = 0.0) -> float:
    resolved = as_float(value)
    return default if resolved is None else resolved


def as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on", "sim"}


def map_pagination(raw: Any) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    page = as_int(source.get("page"), 1)
    total_pages = as_int(source.get("total_pages"), 0)
    return {
        "page": page,
        "pageSize": as_int(source.get("page_size"), 0),
        "totalItems": as_int(source.get("total_items"), 0),
        "totalPages": total_pages,
        "hasNext": as_bool(source.get("has_next")),
        "hasPrevious": as_bool(source.get("has_previous")),
        "isComplete": as_bool(
            source.get("is_complete"),
            default=(page >= total_pages if total_pages else True),
        ),
    }


def map_sort(raw: Any, *, default_by: str, default_dir: str = "desc") -> dict[str, str]:
    source = raw if isinstance(raw, dict) else {}
    return {
        "sortBy": as_text(source.get("sort_by")) or default_by,
        "sortDir": as_text(source.get("sort_dir")) or default_dir,
    }
