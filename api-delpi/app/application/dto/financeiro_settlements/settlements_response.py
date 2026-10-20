"""Response DTOs for financial settlement events (FK1/FK2).

Contract decisions (doc 48 §9-§11):
- ``settlementAmount`` is a decimal-preserving string, never summed across
  currencies;
- ``branchCode`` stays ``None`` when no trustworthy branch exists — never a
  fabricated ``"01"``/``"02"``/``"all"`` (D3.1);
- ``movementType``/``paymentDirection`` are raw source codes (BA/ES/VL/CP,
  R/P) without assigned semantics (D4 pending);
- ``linkStatus`` makes missing document/nature explicit instead of silently
  dropping rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LINK_RESOLVED = "resolved"
LINK_MISSING_DOCUMENT = "missing_document"
LINK_MISSING_NATURE = "missing_nature"
LINK_MISSING_BOTH = "missing_document_and_nature"


@dataclass(slots=True)
class SettlementItem:
    settlementId: str
    settlementDate: str | None
    settlementAmount: str
    currencyCode: str | None
    natureCode: str | None
    natureDescription: str | None
    documentNumber: str | None
    prefix: str | None
    installment: str | None
    documentType: str | None
    partyCode: str | None
    partyStore: str | None
    partyName: str | None
    issueDate: str | None
    dueDate: str | None
    history: str | None
    movementType: str | None
    paymentDirection: str | None
    branchCode: str | None
    branchResolution: str
    linkStatus: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "settlementId": self.settlementId,
            "settlementDate": self.settlementDate,
            "settlementAmount": self.settlementAmount,
            "currencyCode": self.currencyCode,
            "natureCode": self.natureCode,
            "natureDescription": self.natureDescription,
            "documentNumber": self.documentNumber,
            "prefix": self.prefix,
            "installment": self.installment,
            "documentType": self.documentType,
            "partyCode": self.partyCode,
            "partyStore": self.partyStore,
            "partyName": self.partyName,
            "issueDate": self.issueDate,
            "dueDate": self.dueDate,
            "history": self.history,
            "movementType": self.movementType,
            "paymentDirection": self.paymentDirection,
            "branchCode": self.branchCode,
            "branchResolution": self.branchResolution,
            "linkStatus": self.linkStatus,
        }


@dataclass(slots=True)
class SettlementQuality:
    missingDocumentCount: int = 0
    missingNatureCount: int = 0
    unresolvedBranchCount: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "missingDocumentCount": self.missingDocumentCount,
            "missingNatureCount": self.missingNatureCount,
            "unresolvedBranchCount": self.unresolvedBranchCount,
        }


@dataclass(slots=True)
class SettlementsListResponse:
    report: str
    side: str
    period: dict[str, str]
    status: str
    quality: SettlementQuality
    pagination: dict[str, Any]
    sort: dict[str, str]
    items: list[SettlementItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "side": self.side,
            "period": self.period,
            "status": self.status,
            "officialTotals": False,
            "quality": self.quality.to_dict(),
            "pagination": self.pagination,
            "sort": self.sort,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass(slots=True)
class SettlementSummaryGroup:
    side: str
    currencyCode: str | None
    natureCode: str | None
    natureDescription: str | None
    movementType: str | None
    eventCount: int
    totalAmount: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "side": self.side,
            "currencyCode": self.currencyCode,
            "natureCode": self.natureCode,
            "natureDescription": self.natureDescription,
            "movementType": self.movementType,
            "eventCount": self.eventCount,
            "totalAmount": self.totalAmount,
        }


@dataclass(slots=True)
class SettlementsSummaryResponse:
    report: str
    period: dict[str, str]
    status: str
    quality: SettlementQuality
    groups: list[SettlementSummaryGroup] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "period": self.period,
            "status": self.status,
            "officialTotals": False,
            "quality": self.quality.to_dict(),
            "groups": [group.to_dict() for group in self.groups],
        }
