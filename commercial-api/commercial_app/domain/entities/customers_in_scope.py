"""Clientes do escopo de carteira (Minha carteira) + métricas de pedido em aberto."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerInScopeItem:
    customer_code: str
    customer_store: str
    customer_name: str | None
    open_value: float
    has_overdue: bool
    has_open_orders: bool


@dataclass(frozen=True, slots=True)
class CustomersInScopeResult:
    items: tuple[CustomerInScopeItem, ...]
    empty_portfolio: bool
    message: str | None
    metrics_available: bool
    metrics_reason: str | None

    @property
    def customer_count(self) -> int:
        return len(self.items)

    @property
    def open_value_total(self) -> float:
        return sum(item.open_value for item in self.items)

    @property
    def overdue_customer_count(self) -> int:
        return sum(1 for item in self.items if item.has_overdue)
