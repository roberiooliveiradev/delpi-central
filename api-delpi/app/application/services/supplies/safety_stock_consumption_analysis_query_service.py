"""Carrega, enriquece e filtra a análise de consumo × ESTSEG."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockConsumptionAnalysisQueryRequest,
)
from app.application.services.supplies.safety_stock_consumption_analysis_cache import (
    consumption_analysis_cache_key,
    get_cached_consumption_analysis,
    set_cached_consumption_analysis,
)
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.safety_stock_consumption_analysis_service import (
    SafetyStockConsumptionAnalysisService,
)


class SafetyStockConsumptionAnalysisQueryService:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def load_enriched_items(
        self,
        request: SafetyStockConsumptionAnalysisQueryRequest,
        *,
        as_of: date | None = None,
    ) -> tuple[list[dict[str, Any]], date, date, int]:
        period_start, period_end, period_business_days = (
            SafetyStockConsumptionAnalysisService.resolve_period(as_of=as_of)
        )
        cache_key = consumption_analysis_cache_key(
            request,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
        )
        cached = get_cached_consumption_analysis(cache_key)
        if cached is not None:
            items = cached
        else:
            raw_rows = self._repository.fetch_consumption_analysis_rows(
                branch=request.branch,
                period_start=period_start.strftime("%Y%m%d"),
                include_blocked=request.include_blocked,
                product_group=request.product_group,
                unit=request.unit,
                search=request.search,
                product_code=None,
            )
            items = [
                SafetyStockConsumptionAnalysisService.enrich_row(
                    row,
                    period_start=period_start,
                    period_end=period_end,
                    period_business_days=period_business_days,
                    as_of=period_end,
                )
                for row in raw_rows
            ]
            set_cached_consumption_analysis(cache_key, items)

        if request.analysis_status:
            items = [
                item
                for item in items
                if item.get("analysis_status") == request.analysis_status
            ]
        return items, period_start, period_end, period_business_days

    @staticmethod
    def sort_items(
        items: list[dict[str, Any]],
        *,
        sort_by: str,
        sort_direction: str,
    ) -> list[dict[str, Any]]:
        reverse = sort_direction.lower() == "desc"

        def sort_key(item: dict[str, Any]) -> tuple:
            value = item.get(sort_by)
            product_code = str(item.get("product_code") or "")
            if value is None:
                return (1, 0, product_code)
            if isinstance(value, (int, float)):
                return (0, float(value), product_code)
            return (0, str(value).lower(), product_code)

        return sorted(items, key=sort_key, reverse=reverse)
