"""Response DTOs for the R11 billing-exclusion roster (doc 126 §§16/17).

Monetary policy: every quantity/value is a decimal string quantized at
the producer — ``totalValue`` at 2dp (the artifact grain is the SD2 item
``D2_TOTAL``), totals never summed in clients and never blended across
listing populations.

Findings follow the doc 126 §16.3 model: every alert is
``POSSIBLE_DIVERGENCE`` — never ``CONFIRMED_ERROR`` — and carries the
ERP references needed for a human review in TOTVS/Protheus. Membership
in the roster never implies exclusion from CPV/billing/DRE (D-02, E11a).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_TEST_NOT_RUN,
)


@dataclass(slots=True)
class BillingExclusionItem:
    """One SD2 billing line — the artifact grain (doc 126 §2)."""

    lineId: int
    branchCode: str
    document: str
    series: str | None
    item: str | None
    productCode: str
    productDescription: str | None
    productType: str | None
    productGroup: str | None
    tes: str | None
    tesDescription: str | None
    cf: str | None
    customerCode: str | None
    customerStore: str | None
    customerName: str | None
    accountCode: str | None
    warehouse: str | None
    orderNumber: str | None
    issueDate: str
    quantity: str
    unitPrice: str
    totalValue: str
    stockCost: str
    tesStockMovement: str | None
    tesDuplicateFlag: str | None
    documentItemCount: int
    hasStockSiblingItem: bool
    selectionStatus: str
    costStatus: str
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineId": self.lineId,
            "branchCode": self.branchCode,
            "document": self.document,
            "series": self.series,
            "item": self.item,
            "productCode": self.productCode,
            "productDescription": self.productDescription,
            "productType": self.productType,
            "productGroup": self.productGroup,
            "tes": self.tes,
            "tesDescription": self.tesDescription,
            "cf": self.cf,
            "customerCode": self.customerCode,
            "customerStore": self.customerStore,
            "customerName": self.customerName,
            "accountCode": self.accountCode,
            "warehouse": self.warehouse,
            "orderNumber": self.orderNumber,
            "issueDate": self.issueDate,
            "quantity": self.quantity,
            "unitPrice": self.unitPrice,
            "totalValue": self.totalValue,
            "stockCost": self.stockCost,
            "tesStockMovement": self.tesStockMovement,
            "tesDuplicateFlag": self.tesDuplicateFlag,
            "documentItemCount": self.documentItemCount,
            "hasStockSiblingItem": self.hasStockSiblingItem,
            "selectionStatus": self.selectionStatus,
            "costStatus": self.costStatus,
            "findings": list(self.findings),
        }


@dataclass(slots=True)
class BillingExclusionFinding:
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
            "reportId": "R11",
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
class BillingExclusionSummary:
    totalValue: str
    lineCount: int
    documentCount: int
    customerCount: int
    zeroCostCount: int
    missingStockSiblingDocumentCount: int
    findingCount: int
    candidateLineCount: int
    outOfCriteriaLineCount: int
    byTes: list[dict[str, Any]] = field(default_factory=list)
    byProductGroup: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "totalValue": self.totalValue,
            "lineCount": self.lineCount,
            "documentCount": self.documentCount,
            "customerCount": self.customerCount,
            "zeroCostCount": self.zeroCostCount,
            "missingStockSiblingDocumentCount": (
                self.missingStockSiblingDocumentCount
            ),
            "findingCount": self.findingCount,
            "candidateLineCount": self.candidateLineCount,
            "outOfCriteriaLineCount": self.outOfCriteriaLineCount,
            "byTes": self.byTes,
            "byProductGroup": self.byProductGroup,
        }


@dataclass(slots=True)
class BillingExclusionRosterResponse:
    report: str
    period: str
    branchCode: str
    view: str
    status: str
    selection: dict[str, Any]
    pagination: dict[str, Any]
    summary: BillingExclusionSummary | None = None
    findings: list[BillingExclusionFinding] = field(default_factory=list)
    findingsTruncated: bool = False
    rulesCatalog: list[dict[str, Any]] = field(default_factory=list)
    parityStatus: str = PARITY_STATUS_TEST_NOT_RUN
    parityNotes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    items: list[BillingExclusionItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "reportId": "R11",
            "period": self.period,
            "branchCode": self.branchCode,
            "view": self.view,
            "source": "protheus_sd2_sf4_sb1_sa1",
            "officialR11": False,
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
