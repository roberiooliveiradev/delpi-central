# app/domain/entities/commercial/rol_by_product.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class RolByProductItem:
    product_code: str
    product_group: str
    product_name: str
    domestic_rol: float
    export_rol: float
    rol: float
    domestic_gross_revenue: float = 0.0
    export_gross_revenue: float = 0.0
    gross_revenue: float = 0.0
    share_pct: Optional[float] = None
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "product_group": self.product_group,
            "product_name": self.product_name,
            "domestic_rol": self.domestic_rol,
            "export_rol": self.export_rol,
            "rol": self.rol,
            "domestic_gross_revenue": self.domestic_gross_revenue,
            "export_gross_revenue": self.export_gross_revenue,
            "gross_revenue": self.gross_revenue,
            "share_pct": self.share_pct,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class RolByProductResult:
    branch: str
    start_date: str
    end_date: str
    group_by: str
    market: str | None
    items: tuple[RolByProductItem, ...]
    export_destination_countries: tuple[str, ...]
    total_rol: float
    total_gross_revenue: float
    items_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "group_by": self.group_by,
            "market": self.market,
            "items": [item.to_dict() for item in self.items],
            "export_destination_countries": list(self.export_destination_countries),
            "summary": {
                "total_rol": self.total_rol,
                "total_gross_revenue": self.total_gross_revenue,
                "items_count": self.items_count,
            },
        }
