"""Monta uma linha por cliente do membership com left-join de métricas OV."""

from __future__ import annotations

from typing import Sequence

from commercial_app.domain.entities.customers_in_scope import (
    CustomerInScopeItem,
    CustomersInScopeResult,
)
from commercial_app.domain.entities.seller_portfolio import SellerCustomerAssignment
from commercial_app.domain.ports.open_orders_metrics_port import CustomerOpenOrderMetric
from commercial_app.domain.services.seller_portfolio_coverage_audit_service import (
    customer_coverage_key,
)

_METRICS_FETCH_FAILED = "open_orders_metrics_fetch_failed"


class ListCustomersInScopeService:
    """Universo = membership; métricas OV opcionais (zero se ausentes)."""

    def build(
        self,
        assignments: Sequence[SellerCustomerAssignment],
        metrics: Sequence[CustomerOpenOrderMetric] | None = None,
        *,
        empty_portfolio: bool = False,
        message: str | None = None,
        metrics_available: bool = True,
        metrics_reason: str | None = None,
    ) -> CustomersInScopeResult:
        index: dict[tuple[str, str], CustomerOpenOrderMetric] = {}
        for metric in metrics or ():
            key = customer_coverage_key(metric.customer_code, metric.customer_store)
            if key[0] and key[1]:
                index[key] = metric

        seen: set[tuple[str, str, str]] = set()
        items: list[CustomerInScopeItem] = []
        for assignment in assignments:
            key = customer_coverage_key(assignment.customer_code, assignment.customer_store)
            center = str(assignment.customer_center or "").strip()
            identity = (key[0], key[1], center)
            if not key[0] or not key[1] or identity in seen:
                continue
            seen.add(identity)
            metric = index.get(key) if not center else None
            open_value = float(metric.open_value) if metric is not None else 0.0
            has_overdue = bool(metric.has_overdue) if metric is not None else False
            name = None
            if assignment.customer_name and str(assignment.customer_name).strip():
                name = str(assignment.customer_name).strip()
            elif metric is not None and metric.customer_name:
                name = str(metric.customer_name).strip() or None
            items.append(
                CustomerInScopeItem(
                    customer_code=key[0],
                    customer_store=key[1],
                    customer_name=name,
                    open_value=open_value,
                    has_overdue=has_overdue,
                    has_open_orders=open_value > 0 or has_overdue,
                    customer_center=center or None,
                )
            )

        items.sort(
            key=lambda item: (
                item.customer_name or "",
                item.customer_code,
                item.customer_store,
                item.customer_center or "",
            )
        )
        reason = metrics_reason
        if not metrics_available and reason is None:
            reason = _METRICS_FETCH_FAILED
        return CustomersInScopeResult(
            items=tuple(items),
            empty_portfolio=bool(empty_portfolio) and not items,
            message=message,
            metrics_available=bool(metrics_available),
            metrics_reason=None if metrics_available else reason,
        )
