"""Response DTOs for the R05 stock-movements summary (MATR320 rule).

Contract decisions (doc 85 §5 / doc 119 sibling contract):
- amounts are decimal-preserving strings computed in SQL — never summed
  in the frontend and never labelled as an official currency total;
- ``openingBalance`` is a DERIVED column (BR-R05-006): closing balance
  minus the net signed movement of the competence — never a stored
  opening balance;
- ``processTransfers`` is a memo column (BR-R05-005/012): transfers to
  the process warehouse stay inside the branch stock — excluded from
  the balance equation;
- balances stay ``None`` when the SB9 month-end snapshot does not
  exist — a missing snapshot never renders as a fabricated ``0.00``;
- ``officialMatr320`` stays ``False`` and ``parityStatus`` is
  ``PENDING`` until per-competence parity against a new official
  MATR320/MAT056 emission is certified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_TEST_NOT_RUN,
)


@dataclass(slots=True)
class StockMovementsTypeRow:
    productType: str | None
    openingBalance: str | None
    purchases: str
    internalMovements: str
    productionRequisitions: str
    transfers: str
    production: str
    sales: str
    processTransfersMemo: str
    salesReturns: str
    purchaseReturns: str
    thirdPartyIn: str
    thirdPartyOut: str
    closingBalance: str | None
    netMovement: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "productType": self.productType,
            "openingBalance": self.openingBalance,
            "purchases": self.purchases,
            "internalMovements": self.internalMovements,
            "productionRequisitions": self.productionRequisitions,
            "transfers": self.transfers,
            "production": self.production,
            "sales": self.sales,
            "processTransfersMemo": self.processTransfersMemo,
            "salesReturns": self.salesReturns,
            "purchaseReturns": self.purchaseReturns,
            "thirdPartyIn": self.thirdPartyIn,
            "thirdPartyOut": self.thirdPartyOut,
            "closingBalance": self.closingBalance,
            "netMovement": self.netMovement,
        }


@dataclass(slots=True)
class StockMovementsResponse:
    report: str
    period: str
    referenceDate: str
    dataAsOf: str | None
    branchCode: str
    reportScope: str
    status: str
    branchesAvailable: list[str]
    branchesMissing: list[str]
    rows: list[StockMovementsTypeRow] = field(default_factory=list)
    totals: dict[str, Any] = field(default_factory=dict)
    parityStatus: str = PARITY_STATUS_TEST_NOT_RUN
    parityNotes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "period": self.period,
            "referenceDate": self.referenceDate,
            "dataAsOf": self.dataAsOf,
            "branchCode": self.branchCode,
            "reportScope": self.reportScope,
            "source": "protheus_sd1_sd2_sd3_sf4_sb9_sb1",
            "officialMatr320": False,
            "parityStatus": self.parityStatus,
            "parityNotes": self.parityNotes,
            "provenance": self.provenance,
            "status": self.status,
            "branchesAvailable": self.branchesAvailable,
            "branchesMissing": self.branchesMissing,
            "rows": [row.to_dict() for row in self.rows],
            "totals": self.totals,
        }
