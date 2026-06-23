from __future__ import annotations

from typing import Any

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.composition.query_cache_composer import build_query_cache


def financial_rol_cache_key(request: GetRolRequest) -> str:
    return "|".join(
        [
            "financial-rol",
            request.branch or "",
            request.start_date or "",
            request.end_date or "",
            request.customer_segment or "",
        ]
    )


def get_cached_financial_rol(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_financial_rol(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
