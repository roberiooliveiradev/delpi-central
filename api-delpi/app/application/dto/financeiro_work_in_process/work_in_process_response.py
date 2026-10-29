"""Response DTOs for the R08 work-in-process report (MATR989 rule).

Contract decisions (doc 80 §41 / doc 85 §12 BR-R08):
- ``grandTotal`` = process-warehouse physical stock (SB9 ``B9_LOCAL``
  99) + MATR989 allocated balance (SD3 ``RE* − DE*`` on orders alive at
  the emission-day cutoff) — the same parcels the P7 engine certifies
  as EM PROCESSO, exposed standalone for the H02 operand;
- detail ``items`` are the com-OP allocated rows; the sem-OP physical
  block is the identical row set already exposed by the sibling
  stock-inventory report under ``warehouse=99`` — it is summarized
  per type, not duplicated item-by-item;
- amounts are decimal-preserving strings; ``None`` means the measure
  does not exist (missing snapshot), never a fabricated ``0.00``;
- ``officialMatr989`` stays ``False`` and ``parityStatus`` is
  ``PENDING`` until per-competence parity against a new official
  MATR989 emission is certified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_TEST_NOT_RUN,
)


@dataclass(slots=True)
class WorkInProcessItem:
    branchCode: str | None
    productCode: str
    description: str | None
    productType: str | None
    productionOrder: str | None
    allocatedQuantity: str
    allocatedValue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "branchCode": self.branchCode,
            "productCode": self.productCode,
            "description": self.description,
            "productType": self.productType,
            "productionOrder": self.productionOrder,
            "allocatedQuantity": self.allocatedQuantity,
            "allocatedValue": self.allocatedValue,
        }


@dataclass(slots=True)
class WorkInProcessTypeSummary:
    productType: str | None
    physicalValue: str
    allocatedValue: str
    totalValue: str
    openOrderCount: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "productType": self.productType,
            "physicalValue": self.physicalValue,
            "allocatedValue": self.allocatedValue,
            "totalValue": self.totalValue,
            "openOrderCount": self.openOrderCount,
        }


@dataclass(slots=True)
class WorkInProcessResponse:
    report: str
    period: str
    referenceDate: str
    dataAsOf: str | None
    branchCode: str
    reportScope: str
    status: str
    branchesAvailable: list[str]
    branchesMissing: list[str]
    physicalTotal: str | None
    allocatedTotal: str | None
    grandTotal: str | None
    pagination: dict[str, Any]
    parityStatus: str = PARITY_STATUS_TEST_NOT_RUN
    parityNotes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    items: list[WorkInProcessItem] = field(default_factory=list)
    summariesByType: list[WorkInProcessTypeSummary] = field(
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
            "source": "protheus_sb9_sd3_sc2_sb1",
            "officialMatr989": False,
            "parityStatus": self.parityStatus,
            "parityNotes": self.parityNotes,
            "provenance": self.provenance,
            "status": self.status,
            "branchesAvailable": self.branchesAvailable,
            "branchesMissing": self.branchesMissing,
            "physicalTotal": self.physicalTotal,
            "allocatedTotal": self.allocatedTotal,
            "grandTotal": self.grandTotal,
            "pagination": self.pagination,
            "items": [item.to_dict() for item in self.items],
            "summariesByType": [
                row.to_dict() for row in self.summariesByType
            ],
        }
