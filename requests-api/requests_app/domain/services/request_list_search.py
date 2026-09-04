"""List search helpers for mine / work-queue (E11)."""

from __future__ import annotations

from typing import Any

SEARCH_PAYLOAD_KEYS = ("party_name", "party_code", "description")
MIN_SEARCH_LENGTH = 2


def normalize_list_search_query(q: str | None) -> str | None:
    raw = str(q or "").strip()
    if len(raw) < MIN_SEARCH_LENGTH:
        return None
    return raw


def ilike_contains_pattern(q: str) -> str:
    """Build a LIKE pattern with %/_ escaped (use with ESCAPE '\\')."""
    escaped = (
        str(q)
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


def request_matches_search(
    *,
    request_number: str | None,
    payload: dict[str, Any] | None,
    q: str,
) -> bool:
    needle = q.casefold()
    if needle in str(request_number or "").casefold():
        return True
    data = payload if isinstance(payload, dict) else {}
    for key in SEARCH_PAYLOAD_KEYS:
        if needle in str(data.get(key) or "").casefold():
            return True
    return False
