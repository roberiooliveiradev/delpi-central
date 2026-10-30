"""Response DTOs for the R06 stock-kardex query (doc 122 §4).

Monetary policy (BR-R06-012): every quantity/value is a decimal string
quantized at 6dp — computed at the data owner, never summed in clients.
``openingQuantity``/``openingValue`` stay ``None`` when the previous
month-end SB9 snapshot is missing for the block — a missing opening
balance never renders as a fabricated zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_TEST_NOT_RUN,
)


@dataclass(slots=True)
class StockKardexMovement:
    """One MATR910 movement line — the artifact grain (doc 122 §5.4)."""

    sourceTable: str
    movementId: int
    branchCode: str
    warehouse: str
    productCode: str
    description: str | None
    productType: str | None
    unit: str | None
    document: str
    series: str | None
    movementDate: str
    sequence: str | None
    tm: str | None
    cf: str | None
    reference: str | None
    movementKind: str
    isReturn: bool
    documentType: str | None
    entryQuantity: str
    entryValue: str
    outputQuantity: str
    outputValue: str
    unitCost: str | None
    costAsOfSource: str
    runningQuantity: str | None
    runningValue: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceTable": self.sourceTable,
            "movementId": self.movementId,
            "branchCode": self.branchCode,
            "warehouse": self.warehouse,
            "productCode": self.productCode,
            "description": self.description,
            "productType": self.productType,
            "unit": self.unit,
            "document": self.document,
            "series": self.series,
            "movementDate": self.movementDate,
            "sequence": self.sequence,
            "tm": self.tm,
            "cf": self.cf,
            "reference": self.reference,
            "movementKind": self.movementKind,
            "isReturn": self.isReturn,
            "documentType": self.documentType,
            "entryQuantity": self.entryQuantity,
            "entryValue": self.entryValue,
            "outputQuantity": self.outputQuantity,
            "outputValue": self.outputValue,
            "unitCost": self.unitCost,
            "costAsOfSource": self.costAsOfSource,
            "runningQuantity": self.runningQuantity,
            "runningValue": self.runningValue,
        }


@dataclass(slots=True)
class StockKardexBlock:
    """One MATR910 product block — opening balance + movement totals +
    computed closing for (branch, warehouse, product)."""

    productCode: str
    description: str | None
    productType: str | None
    unit: str | None
    branchCode: str
    warehouse: str
    openingQuantity: str | None
    openingValue: str | None
    entryQuantityTotal: str
    entryValueTotal: str
    outputQuantityTotal: str
    outputValueTotal: str
    closingQuantity: str | None
    closingValue: str | None
    movementCount: int
    hasOpeningSnapshot: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "productCode": self.productCode,
            "description": self.description,
            "productType": self.productType,
            "unit": self.unit,
            "branchCode": self.branchCode,
            "warehouse": self.warehouse,
            "openingQuantity": self.openingQuantity,
            "openingValue": self.openingValue,
            "entryQuantityTotal": self.entryQuantityTotal,
            "entryValueTotal": self.entryValueTotal,
            "outputQuantityTotal": self.outputQuantityTotal,
            "outputValueTotal": self.outputValueTotal,
            "closingQuantity": self.closingQuantity,
            "closingValue": self.closingValue,
            "movementCount": self.movementCount,
            "hasOpeningSnapshot": self.hasOpeningSnapshot,
        }


@dataclass(slots=True)
class StockKardexWarehouseSummary:
    branchCode: str
    warehouse: str
    movementCount: int
    entryQuantity: str
    entryValue: str
    outputQuantity: str
    outputValue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "branchCode": self.branchCode,
            "warehouse": self.warehouse,
            "movementCount": self.movementCount,
            "entryQuantity": self.entryQuantity,
            "entryValue": self.entryValue,
            "outputQuantity": self.outputQuantity,
            "outputValue": self.outputValue,
        }


@dataclass(slots=True)
class StockKardexTypeSummary:
    productType: str | None
    movementCount: int
    entryQuantity: str
    entryValue: str
    outputQuantity: str
    outputValue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "productType": self.productType,
            "movementCount": self.movementCount,
            "entryQuantity": self.entryQuantity,
            "entryValue": self.entryValue,
            "outputQuantity": self.outputQuantity,
            "outputValue": self.outputValue,
        }


@dataclass(slots=True)
class StockKardexTopProduct:
    productCode: str
    description: str | None
    movementCount: int
    outputValue: str
    outputQuantity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "productCode": self.productCode,
            "description": self.description,
            "movementCount": self.movementCount,
            "outputValue": self.outputValue,
            "outputQuantity": self.outputQuantity,
        }


@dataclass(slots=True)
class StockKardexTotals:
    movementCount: int
    blockCount: int
    entryQuantity: str
    entryValue: str
    outputQuantity: str
    outputValue: str
    netQuantity: str
    netValue: str
    openingValue: str | None
    closingValue: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "movementCount": self.movementCount,
            "blockCount": self.blockCount,
            "entryQuantity": self.entryQuantity,
            "entryValue": self.entryValue,
            "outputQuantity": self.outputQuantity,
            "outputValue": self.outputValue,
            "netQuantity": self.netQuantity,
            "netValue": self.netValue,
            "openingValue": self.openingValue,
            "closingValue": self.closingValue,
        }


@dataclass(slots=True)
class StockKardexResponse:
    report: str
    period: str
    referenceDate: str
    dataAsOf: str | None
    branchCode: str
    warehouse: str | None
    documentKind: str
    productCode: str | None
    status: str
    branchesAvailable: list[str]
    branchesMissing: list[str]
    pagination: dict[str, Any]
    totals: StockKardexTotals | None = None
    parityStatus: str = PARITY_STATUS_TEST_NOT_RUN
    parityNotes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    items: list[StockKardexMovement] = field(default_factory=list)
    blocks: list[StockKardexBlock] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "period": self.period,
            "referenceDate": self.referenceDate,
            "dataAsOf": self.dataAsOf,
            "branchCode": self.branchCode,
            "warehouse": self.warehouse,
            "documentKind": self.documentKind,
            "productCode": self.productCode,
            "source": "protheus_sd1_sd2_sd3_sf4_sb9_ttat_sb1",
            "officialR06": False,
            "parityStatus": self.parityStatus,
            "parityNotes": self.parityNotes,
            "provenance": self.provenance,
            "status": self.status,
            "branchesAvailable": self.branchesAvailable,
            "branchesMissing": self.branchesMissing,
            "pagination": self.pagination,
            "totals": self.totals.to_dict() if self.totals else None,
            "items": [item.to_dict() for item in self.items],
            "blocks": [block.to_dict() for block in self.blocks],
        }


@dataclass(slots=True)
class StockKardexSummaryResponse:
    report: str
    period: str
    referenceDate: str
    dataAsOf: str | None
    branchCode: str
    warehouse: str | None
    documentKind: str
    status: str
    branchesAvailable: list[str]
    branchesMissing: list[str]
    totals: StockKardexTotals | None = None
    parityStatus: str = PARITY_STATUS_TEST_NOT_RUN
    parityNotes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    summariesByType: list[StockKardexTypeSummary] = field(default_factory=list)
    summariesByWarehouse: list[StockKardexWarehouseSummary] = field(
        default_factory=list
    )
    topProductsByCost: list[StockKardexTopProduct] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "period": self.period,
            "referenceDate": self.referenceDate,
            "dataAsOf": self.dataAsOf,
            "branchCode": self.branchCode,
            "warehouse": self.warehouse,
            "documentKind": self.documentKind,
            "source": "protheus_sd1_sd2_sd3_sf4_sb9_ttat_sb1",
            "officialR06": False,
            "parityStatus": self.parityStatus,
            "parityNotes": self.parityNotes,
            "provenance": self.provenance,
            "status": self.status,
            "branchesAvailable": self.branchesAvailable,
            "branchesMissing": self.branchesMissing,
            "totals": self.totals.to_dict() if self.totals else None,
            "summariesByType": [
                row.to_dict() for row in self.summariesByType
            ],
            "summariesByWarehouse": [
                row.to_dict() for row in self.summariesByWarehouse
            ],
            "topProductsByCost": [
                row.to_dict() for row in self.topProductsByCost
            ],
        }
