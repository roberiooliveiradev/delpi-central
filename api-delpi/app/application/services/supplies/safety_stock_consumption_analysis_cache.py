"""Cache da análise de consumo × estoque de segurança."""

from __future__ import annotations

from typing import Any

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockConsumptionAnalysisQueryRequest,
)
from app.composition.query_cache_composer import build_query_cache


def consumption_analysis_cache_key(
    request: SafetyStockConsumptionAnalysisQueryRequest,
    *,
    period_start: str,
    period_end: str,
) -> str:
    return "|".join(
        [
            "safety-stock-consumption-analysis",
            request.branch or "",
            period_start,
            period_end,
            "blocked" if request.include_blocked else "active",
            request.product_group or "",
            request.unit or "",
            request.search or "",
        ]
    )


def get_cached_consumption_analysis(key: str) -> list[dict[str, Any]] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, list):
        return cached
    return None


def set_cached_consumption_analysis(key: str, value: list[dict[str, Any]]) -> None:
    build_query_cache().set(key, value)
