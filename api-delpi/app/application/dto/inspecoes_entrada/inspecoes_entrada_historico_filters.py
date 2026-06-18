from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InspecoesEntradaHistoricoFilters:
    result: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    supplier: str | None = None
    product_code: str | None = None
    inspector: str | None = None
    invoice_number: str | None = None
    lot: str | None = None

    def to_dict(self) -> dict:
        return {
            "result": self.result,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "supplier": self.supplier,
            "product_code": self.product_code,
            "inspector": self.inspector,
            "invoice_number": self.invoice_number,
            "lot": self.lot,
        }
