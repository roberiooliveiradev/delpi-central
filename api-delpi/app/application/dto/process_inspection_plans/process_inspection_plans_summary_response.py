from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProcessInspectionPlansSummaryResponse:
    branch: str
    products_without_plan: int
    orders_without_plan: int
    total_open_orders: int
    orders_with_plan: int
    registered_pct: float
    distribution: list[dict]

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "products_without_plan": self.products_without_plan,
            "orders_without_plan": self.orders_without_plan,
            "total_open_orders": self.total_open_orders,
            "orders_with_plan": self.orders_with_plan,
            "registered_pct": self.registered_pct,
            "distribution": list(self.distribution),
        }
