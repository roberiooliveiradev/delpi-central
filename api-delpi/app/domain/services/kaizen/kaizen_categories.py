from __future__ import annotations

from typing import Any

_MAX_CATEGORIES = 10
_MAX_LABEL_LENGTH = 50


def normalize_categories(
    raw: Any,
    *,
    legacy_category: Any = None,
) -> list[str]:
    """Normaliza categorias (lista, legado string ou vazio) com deduplicação."""
    items: list[str] = []
    if isinstance(raw, list):
        items = [str(value).strip() for value in raw if str(value).strip()]
    elif isinstance(raw, str) and raw.strip():
        items = [raw.strip()]

    if not items and legacy_category is not None and str(legacy_category).strip():
        items = [str(legacy_category).strip()]

    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        key = item.casefold()
        if key in seen or len(item) > _MAX_LABEL_LENGTH:
            continue
        seen.add(key)
        normalized.append(item)
        if len(normalized) >= _MAX_CATEGORIES:
            break
    return normalized


def categories_from_row(row: dict[str, Any]) -> list[str]:
    stored = row.get("categories")
    if stored:
        return normalize_categories(stored)
    return normalize_categories(None, legacy_category=row.get("category"))
