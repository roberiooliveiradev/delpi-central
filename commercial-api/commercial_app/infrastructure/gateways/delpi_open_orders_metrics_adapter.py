from __future__ import annotations

import logging
from typing import Any, Sequence

from commercial_app.domain.ports.open_orders_metrics_port import (
    CustomerOpenOrderMetric,
    OpenOrdersMetricsPort,
)
from commercial_app.infrastructure.gateways.delpi_commercial_gateway import (
    DelpiCommercialGateway,
)

logger = logging.getLogger("commercial.open_orders_metrics")


class DelpiOpenOrdersMetricsAdapter(OpenOrdersMetricsPort):
    def __init__(self, gateway: DelpiCommercialGateway | None = None) -> None:
        self._gateway = gateway or DelpiCommercialGateway()

    def list_customer_metrics(
        self,
        customer_keys: Sequence[tuple[str, str]] | None = None,
    ) -> list[CustomerOpenOrderMetric]:
        payload: dict[str, Any] = {}
        if customer_keys:
            payload["customers"] = [
                {"customer_code": code, "customer_store": store}
                for code, store in customer_keys
                if str(code or "").strip() and str(store or "").strip()
            ]
        response = self._gateway.list_customer_open_order_metrics(payload=payload)
        data = response.get("data") if isinstance(response, dict) else None
        if not isinstance(data, dict):
            data = response if isinstance(response, dict) else {}
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            return []

        result: list[CustomerOpenOrderMetric] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            code = str(item.get("customer_code") or "").strip()
            store = str(item.get("customer_store") or "").strip()
            if not code or not store:
                continue
            name_raw = item.get("customer_name")
            name = str(name_raw).strip() if name_raw else None
            try:
                open_value = float(item.get("open_value") or 0)
            except (TypeError, ValueError):
                open_value = 0.0
            result.append(
                CustomerOpenOrderMetric(
                    customer_code=code,
                    customer_store=store,
                    customer_name=name or None,
                    open_value=open_value,
                    has_overdue=bool(item.get("has_overdue")),
                )
            )
        return result
