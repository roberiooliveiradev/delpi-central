"""Entidade — matriz de faturamento por cliente × mês."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
    DEFAULT_BILLING_NATURE,
    SUPPORTED_BILLING_NATURES,
)


@dataclass(frozen=True, slots=True)
class BillingByCustomerMonthItem:
    customer_code: str
    customer_store: str
    customer_name: str
    monthly_values: dict[str, float]
    total: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "monthly_values": {
                key: round(float(value), 2)
                for key, value in self.monthly_values.items()
            },
            "total": round(float(self.total), 2),
        }


@dataclass(frozen=True, slots=True)
class BillingByCustomerMonthResult:
    branch: str
    start_date: str
    end_date: str
    nature: str
    months: tuple[str, ...]
    items: tuple[BillingByCustomerMonthItem, ...]
    grand_total: float
    monthly_totals: dict[str, float]
    customers_count: int
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "nature": self.nature,
            "billingNature": self.nature,
            "supportedNatures": list(SUPPORTED_BILLING_NATURES),
            "months": list(self.months),
            "items": [item.to_dict() for item in self.items],
            "summary": {
                "grand_total": round(float(self.grand_total), 2),
                "customers_count": self.customers_count,
                "items_count": len(self.items),
                "monthly_totals": {
                    key: round(float(value), 2)
                    for key, value in self.monthly_totals.items()
                },
                "truncated": self.truncated,
            },
            "defaultNature": DEFAULT_BILLING_NATURE,
        }
