"""Horizon de carteira em aberto por data_entrega (KPI-CARTEIRA-HORIZON)."""

from __future__ import annotations

from datetime import datetime
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
from commercial_app.domain.services.open_orders_horizon_bucket_service import (
    OpenOrdersHorizonBucketService,
)


class GetOpenPortfolioHorizonUseCase:
    def __init__(
        self,
        *,
        filter_service: FilterOpenOrdersByScopeService | None = None,
        bucket_service: OpenOrdersHorizonBucketService | None = None,
    ) -> None:
        self._filter = filter_service or FilterOpenOrdersByScopeService()
        self._buckets = bucket_service or OpenOrdersHorizonBucketService()

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
        items_raw = filtered.get("items")
        items = [item for item in items_raw if isinstance(item, dict)] if isinstance(items_raw, list) else []
        horizon = self._buckets.bucketize(items, as_of=as_of)

        if scope.empty_portfolio:
            mode = "empty"
        elif scope.unrestricted:
            mode = "unrestricted"
        else:
            mode = "membership"

        horizon["scope"] = {
            "seller_id": scope.portfolio_id,
            "mode": mode,
        }
        return horizon
