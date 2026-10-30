"""Response DTOs for the R10 cost-center-expenses query (doc 126 §§16/17).

Monetary policy: every quantity/value is a decimal string quantized at
the producer — ``totalValue`` at 2dp (the artifact grain is the SD1 item
``D1_TOTAL``), totals never summed in clients and never mixed across
universes (doc 127 §3).

Findings follow the doc 126 §16.3 model: every alert is
``POSSIBLE_DIVERGENCE`` — never ``CONFIRMED_ERROR`` — and carries the
ERP references needed for a human review in TOTVS/Protheus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_TEST_NOT_RUN,
)


@dataclass(slots=True)
class CostCenterExpenseItem:
    """One SD1 expense line — the artifact grain (doc 126 §2)."""

    lineId: int
    branchCode: str
    document: str
    series: str | None
    item: str | None
    sequence: str | None
    productCode: str
    productDescription: str | None
    productType: str | None
    productGroup: str | None
    documentType: str | None
    costCenter: str | None
    costCenterDescription: str | None
    accountCode: str | None
    tes: str | None
    cf: str | None
    supplierCode: str | None
    supplierStore: str | None
    supplierName: str | None
    warehouse: str | None
    orderNumber: str | None
    entryDate: str
    issueDate: str | None
    quantity: str
    unitValue: str
    totalValue: str
    universe: str
    calculationExclusion: str | None
    costClass: str
    costCenterCatalogStatus: str
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineId": self.lineId,
            "branchCode": self.branchCode,
            "document": self.document,
            "series": self.series,
            "item": self.item,
            "sequence": self.sequence,
            "productCode": self.productCode,
            "productDescription": self.productDescription,
            "productType": self.productType,
            "productGroup": self.productGroup,
            "documentType": self.documentType,
            "costCenter": self.costCenter,
            "costCenterDescription": self.costCenterDescription,
            "accountCode": self.accountCode,
            "tes": self.tes,
            "cf": self.cf,
            "supplierCode": self.supplierCode,
            "supplierStore": self.supplierStore,
            "supplierName": self.supplierName,
            "warehouse": self.warehouse,
            "orderNumber": self.orderNumber,
            "entryDate": self.entryDate,
            "issueDate": self.issueDate,
            "quantity": self.quantity,
            "unitValue": self.unitValue,
            "totalValue": self.totalValue,
            "universe": self.universe,
            "calculationExclusion": self.calculationExclusion,
            "costClass": self.costClass,
            "costCenterCatalogStatus": self.costCenterCatalogStatus,
            "findings": list(self.findings),
        }


@dataclass(slots=True)
class CostCenterExpenseFinding:
    """One POSSIBLE_DIVERGENCE alert (doc 126 §16.3 model)."""

    findingId: str
    ruleId: str
    status: str
    lineId: int
    sourceRecord: dict[str, Any]
    observedValues: dict[str, Any]
    findingExplanation: str
    evidenceRefs: list[str]
    erpReviewGuidance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "reportId": "R10",
            "findingId": self.findingId,
            "ruleId": self.ruleId,
            "status": self.status,
            "lineId": self.lineId,
            "sourceRecord": self.sourceRecord,
            "observedValues": self.observedValues,
            "findingExplanation": self.findingExplanation,
            "evidenceRefs": list(self.evidenceRefs),
            "erpReviewGuidance": self.erpReviewGuidance,
            "classification": "POSSIBLE_DIVERGENCE",
        }


@dataclass(slots=True)
class CostCenterExpenseSummary:
    totalValue: str
    lineCount: int
    documentCount: int
    costCenterCount: int
    supplierCount: int
    findingCount: int
    unclassifiedCount: int
    byCostCenter: list[dict[str, Any]] = field(default_factory=list)
    byProductType: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "totalValue": self.totalValue,
            "lineCount": self.lineCount,
            "documentCount": self.documentCount,
            "costCenterCount": self.costCenterCount,
            "supplierCount": self.supplierCount,
            "findingCount": self.findingCount,
            "unclassifiedCount": self.unclassifiedCount,
            "byCostCenter": self.byCostCenter,
            "byProductType": self.byProductType,
        }


@dataclass(slots=True)
class CostCenterExpensesResponse:
    report: str
    period: str
    branchCode: str
    universe: str
    view: str
    status: str
    selection: dict[str, Any]
    pagination: dict[str, Any]
    summary: CostCenterExpenseSummary | None = None
    findings: list[CostCenterExpenseFinding] = field(default_factory=list)
    findingsTruncated: bool = False
    rulesCatalog: list[dict[str, Any]] = field(default_factory=list)
    parityStatus: str = PARITY_STATUS_TEST_NOT_RUN
    parityNotes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    items: list[CostCenterExpenseItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "reportId": "R10",
            "period": self.period,
            "branchCode": self.branchCode,
            "universe": self.universe,
            "view": self.view,
            "source": "protheus_sd1_sb1_sa2_ctt",
            "officialR10": False,
            "parityStatus": self.parityStatus,
            "parityNotes": self.parityNotes,
            "provenance": self.provenance,
            "status": self.status,
            "selection": self.selection,
            "pagination": self.pagination,
            "summary": (
                self.summary.to_dict() if self.summary else None
            ),
            "findings": [f.to_dict() for f in self.findings],
            "findingsTruncated": self.findingsTruncated,
            "rulesCatalog": self.rulesCatalog,
            "items": [item.to_dict() for item in self.items],
        }
