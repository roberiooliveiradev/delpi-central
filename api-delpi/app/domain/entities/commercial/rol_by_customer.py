# app/domain/entities/commercial/rol_by_customer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class RolByCustomerItem:
    customer_code: str
    customer_store: str
    customer_name: str
    rol: float
    share_pct: Optional[float]
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "rol": self.rol,
            "share_pct": self.share_pct,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class RolByCustomerResult:
    branch: str
    start_date: str
    end_date: str
    items: tuple[RolByCustomerItem, ...]
    others: Optional[RolByCustomerItem]
    total_rol: float
    customers_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "items": [item.to_dict() for item in self.items],
            "others": self.others.to_dict() if self.others else None,
            "summary": {
                "total_rol": self.total_rol,
                "customers_count": self.customers_count,
                "items_count": len(self.items),
            },
        }
