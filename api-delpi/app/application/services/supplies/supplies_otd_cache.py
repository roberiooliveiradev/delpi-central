from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.otd_physical_receipts import (
    physical_receipts_enabled,
)

from typing import Any

from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.composition.query_cache_composer import build_query_cache


def supplies_otd_cache_key(request: GetOTDRequest) -> str:
    return "|".join(
        [
            "supplies-otd-physical-v1" if physical_receipts_enabled() else "supplies-otd",
            request.branch or "",
            request.start_date or "",
            request.end_date or "",
            str(request.top_limit or 5),
            str(request.details_limit or 20),
        ]
    )


def get_cached_supplies_otd(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_supplies_otd(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
