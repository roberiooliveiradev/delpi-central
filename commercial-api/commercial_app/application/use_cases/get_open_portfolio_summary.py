"""Resumo de carteira em aberto (KPI-CARTEIRA) — sem devolver items."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from commercial_app.application.services.analytics_customer_codes_service import (
    AnalyticsCustomerCodesService,
)
from commercial_app.application.services.filter_open_orders_by_scope_service import (
    FilterOpenOrdersByScopeService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)

NATURE_OPEN_ORDER_VALUE = "open_order_value"


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _summary_from_filtered(filtered: dict[str, Any]) -> tuple[float, int]:
    summary = filtered.get("summary")
    if isinstance(summary, dict) and (
        "valor_total_aberto" in summary or "total_linhas" in summary
    ):
        return (
            _as_float(summary.get("valor_total_aberto")),
            int(summary.get("total_linhas") or 0),
        )
    items_raw = filtered.get("items")
    items = [item for item in items_raw if isinstance(item, dict)] if isinstance(items_raw, list) else []
    open_value = sum(_as_float(item.get("valor_aberto")) for item in items)
    return open_value, len(items)


class GetOpenPortfolioSummaryUseCase:
    """Aplica escopo commercial ao payload open-orders e retorna só o summary KPI."""

    def __init__(
        self,
        *,
        filter_service: FilterOpenOrdersByScopeService | None = None,
    ) -> None:
        self._filter = filter_service or FilterOpenOrdersByScopeService()

    def execute(
        self,
        raw_data: dict[str, Any] | None,
        scope: CommercialCustomerScope,
        *,
        as_of: datetime | None = None,
        selected_customer_codes: str | None = None,
    ) -> dict[str, Any]:
        selected = frozenset(
            AnalyticsCustomerCodesService.parse_codes_csv(selected_customer_codes)
        )
        filtered = self._filter.apply(
            raw_data if isinstance(raw_data, dict) else {},
            scope,
            selected_customer_codes=selected or None,
        )
        open_value, open_line_count = _summary_from_filtered(filtered)
        stamp = as_of or datetime.now(timezone.utc)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return {
            "openValue": open_value,
            "openLineCount": open_line_count,
            "asOf": stamp.isoformat(),
            "nature": NATURE_OPEN_ORDER_VALUE,
        }
