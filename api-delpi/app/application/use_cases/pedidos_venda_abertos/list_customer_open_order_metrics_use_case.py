"""Agrega métricas de pedidos em aberto por cliente (cadastro/loja)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class CustomerOpenOrderMetrics:
    customer_code: str
    customer_store: str
    customer_name: str | None
    open_value: float
    has_overdue: bool

    def to_dict(self) -> dict:
        return {
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "open_value": self.open_value,
            "has_overdue": self.has_overdue,
        }


@dataclass(frozen=True, slots=True)
class ListCustomerOpenOrderMetricsRequest:
    customers: tuple[tuple[str, str], ...] = ()


class ListCustomerOpenOrderMetricsUseCase:
    def __init__(self, repository) -> None:
        self._repository = repository

    def execute(
        self,
        request: ListCustomerOpenOrderMetricsRequest | None = None,
    ) -> list[CustomerOpenOrderMetrics]:
        keys = None
        if request and request.customers:
            keys = [
                (str(code or "").strip(), str(store or "").strip())
                for code, store in request.customers
                if str(code or "").strip() and str(store or "").strip()
            ]
        rows = self._repository.aggregate_customer_open_order_metrics(keys)
        items: list[CustomerOpenOrderMetrics] = []
        for row in rows or []:
            code = str(row.get("customer_code") or "").strip()
            store = str(row.get("customer_store") or "").strip()
            if not code or not store:
                continue
            name_raw = row.get("customer_name")
            name = str(name_raw).strip() if name_raw else None
            try:
                open_value = float(row.get("open_value") or 0)
            except (TypeError, ValueError):
                open_value = 0.0
            has_overdue = bool(row.get("has_overdue"))
            items.append(
                CustomerOpenOrderMetrics(
                    customer_code=code,
                    customer_store=store,
                    customer_name=name or None,
                    open_value=open_value,
                    has_overdue=has_overdue,
                )
            )
        return items
