"""List sort helpers for mine / work-queue.

Contract: `sort=field:dir[,field:dir]` — up to 3 levels, whitelist only.
Parsing is domain-pure; callers map ValueError to their error type.
"""

from __future__ import annotations

LIST_SORT_FIELDS = (
    "created_at",
    "updated_at",
    "request_number",
    "status",
    "type_code",
    "branch",
)
LIST_SORT_MAX_LEVELS = 3
DEFAULT_SORT: tuple[str, str] = ("created_at", "desc")


def parse_list_sort(sort: str | None) -> list[tuple[str, str]] | None:
    """Parse `field:dir,...` into [(field, 'asc'|'desc')] or None when empty.

    Raises ValueError on unknown field, bad direction, duplicate field,
    or more than LIST_SORT_MAX_LEVELS levels.
    """
    raw = str(sort or "").strip()
    if not raw:
        return None
    levels: list[tuple[str, str]] = []
    seen: set[str] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        field, _, direction = chunk.partition(":")
        field = field.strip()
        direction = (direction or "asc").strip()
        if field not in LIST_SORT_FIELDS:
            raise ValueError(f"unknown sort field: {field}")
        if direction not in ("asc", "desc"):
            raise ValueError(f"invalid sort direction: {direction}")
        if field in seen:
            raise ValueError(f"duplicate sort field: {field}")
        seen.add(field)
        levels.append((field, direction))
    if len(levels) > LIST_SORT_MAX_LEVELS:
        raise ValueError("too many sort levels")
    return levels or None


def effective_sort_levels(
    sort_levels: list[tuple[str, str]] | None,
) -> list[tuple[str, str]]:
    """Parsed levels or the canonical default (created_at desc)."""
    return sort_levels if sort_levels else [DEFAULT_SORT]
