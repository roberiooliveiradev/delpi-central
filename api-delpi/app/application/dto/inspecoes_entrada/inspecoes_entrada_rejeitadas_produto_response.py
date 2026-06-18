from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesEntradaRejeitadaProdutoItemResponse:
    branch: str
    inspection_id: str
    report_date: str | None
    report_time: str | None
    invoice_number: str
    supplier_name: str
    product_code: str
    product_description: str | None
    lot: str
    quantity: float
    unit: str

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "inspection_id": self.inspection_id,
            "report_date": self.report_date,
            "report_time": self.report_time,
            "invoice_number": self.invoice_number,
            "supplier_name": self.supplier_name,
            "product_code": self.product_code,
            "product_description": self.product_description,
            "lot": self.lot,
            "quantity": self.quantity,
            "unit": self.unit,
        }


@dataclass
class InspecoesEntradaRejeitadasProdutoResponse:
    branch: str
    items: list[InspecoesEntradaRejeitadaProdutoItemResponse]
    total: int

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "items": [item.to_dict() for item in self.items],
            "total": self.total,
        }
