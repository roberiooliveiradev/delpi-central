from __future__ import annotations

from typing import Any

from app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from app.composition.query_cache_composer import build_query_cache


def inventory_turnover_cache_key(request: GetInventoryTurnoverRequest) -> str:
    return "|".join(
        [
            "inventory-turnover",
            request.branch or "",
            request.location or "",
            request.start_date or "",
            request.end_date or "",
            "strict" if request.strict_idd_period else "relaxed",
        ]
    )


def get_cached_inventory_turnover(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_inventory_turnover(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
