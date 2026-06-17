"""Paginação operacional com detecção de resultado incompleto (TOP N + 1)."""

from __future__ import annotations


def overfetch_limit(limit: int) -> int:
    return max(int(limit), 1) + 1


def trim_overfetched(items: list, limit: int) -> tuple[list, bool]:
    normalized_limit = max(int(limit), 1)

    if len(items) <= normalized_limit:
        return items, True

    return items[:normalized_limit], False


def build_operational_pagination(
    *,
    limit: int,
    offset: int,
    returned: int,
    is_complete: bool,
    total: int | None = None,
) -> dict:
    payload: dict = {
        "limit": limit,
        "offset": offset,
        "returned": returned,
        "is_complete": is_complete,
    }

    if total is not None:
        payload["total"] = total

    return payload
