"""Response DTOs for the R03/P7 stock-inventory snapshot query.

Contract decisions (doc 49 §4):
- amounts are decimal-preserving strings computed in SQL — never summed
  in the frontend and never labelled as an official currency total;
- ``historicalTotal`` stays ``None`` when no snapshot exists — a missing
  snapshot never renders as a fabricated ``0.00``;
- ``officialP7`` is always ``False`` and ``parityStatus`` stays
  ``TEST_NOT_RUN`` until the MATR460 parity evidence exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class StockInventoryItem:
    productCode: str
    description: str | None
    productType: str | None
    productGroup: str | None
    unit: str | None
    warehouse: str | None
    branchCode: str | None
    historicalQuantity: str
    historicalStockValue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "productCode": self.productCode,
            "description": self.description,
            "productType": self.productType,
            "productGroup": self.productGroup,
            "unit": self.unit,
            "warehouse": self.warehouse,
            "branchCode": self.branchCode,
            "historicalQuantity": self.historicalQuantity,
            "historicalStockValue": self.historicalStockValue,
        }


@dataclass(slots=True)
class StockInventoryTypeSummary:
    productType: str | None
    itemCount: int
    totalQuantity: str
    totalStockValue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "productType": self.productType,
            "itemCount": self.itemCount,
            "totalQuantity": self.totalQuantity,
            "totalStockValue": self.totalStockValue,
        }


@dataclass(slots=True)
class StockInventoryWarehouseSummary:
    branchCode: str | None
    warehouse: str | None
    itemCount: int
    totalQuantity: str
    totalStockValue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "branchCode": self.branchCode,
            "warehouse": self.warehouse,
            "itemCount": self.itemCount,
            "totalQuantity": self.totalQuantity,
            "totalStockValue": self.totalStockValue,
        }


@dataclass(slots=True)
class StockInventoryResponse:
    report: str
    period: str
    referenceDate: str
    dataAsOf: str | None
    branchCode: str
    reportScope: str
    status: str
    branchesAvailable: list[str]
    branchesMissing: list[str]
    historicalTotal: str | None
    pagination: dict[str, Any]
    items: list[StockInventoryItem] = field(default_factory=list)
    summariesByType: list[StockInventoryTypeSummary] = field(default_factory=list)
    summariesByWarehouse: list[StockInventoryWarehouseSummary] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "period": self.period,
            "referenceDate": self.referenceDate,
            "dataAsOf": self.dataAsOf,
            "branchCode": self.branchCode,
            "reportScope": self.reportScope,
            "source": "protheus_sb9_sb1",
            "officialP7": False,
            "parityStatus": "TEST_NOT_RUN",
            "status": self.status,
            "branchesAvailable": self.branchesAvailable,
            "branchesMissing": self.branchesMissing,
            "historicalTotal": self.historicalTotal,
            "pagination": self.pagination,
            "items": [item.to_dict() for item in self.items],
            "summariesByType": [group.to_dict() for group in self.summariesByType],
            "summariesByWarehouse": [
                group.to_dict() for group in self.summariesByWarehouse
            ],
        }
