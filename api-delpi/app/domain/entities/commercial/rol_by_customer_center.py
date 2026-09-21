# app/domain/entities/commercial/rol_by_customer_center.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.domain.totvs.protheus_customer_center import (
    UNCLASSIFIED_CUSTOMER_CENTER_NAME,
)


@dataclass(frozen=True, slots=True)
class RolByCustomerCenterItem:
    customer_code: str
    customer_store: str
    customer_name: str
    customer_center: Optional[str]
    customer_center_name: str
    center_active: Optional[bool]
    product_code: str
    product_name: str
    rol: float
    gross_revenue: float
    qty: float
    unit: str | None = None
    mixed_units: bool = False
    share_pct: Optional[float] = None
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "customer_center": self.customer_center,
            "customer_center_name": self.customer_center_name
            or UNCLASSIFIED_CUSTOMER_CENTER_NAME,
            "center_active": self.center_active,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "rol": self.rol,
            "gross_revenue": self.gross_revenue,
            "qty": self.qty,
            "unit": self.unit,
            "mixed_units": self.mixed_units,
            "share_pct": self.share_pct,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class RolByCustomerCenterResult:
    branch: str
    start_date: str
    end_date: str
    group_by: str
    market: str | None
    items: tuple[RolByCustomerCenterItem, ...]
    total_rol: float
    total_gross_revenue: float
    total_qty: float
    items_count: int
    unclassified_rol: float
    unclassified_qty: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "group_by": self.group_by,
            "market": self.market,
            "items": [item.to_dict() for item in self.items],
            "summary": {
                "total_rol": self.total_rol,
                "total_gross_revenue": self.total_gross_revenue,
                "total_qty": self.total_qty,
                "items_count": self.items_count,
                "unclassified_rol": self.unclassified_rol,
                "unclassified_qty": self.unclassified_qty,
            },
        }
