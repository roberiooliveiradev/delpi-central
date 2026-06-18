from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesEntradaPendenteFornecedorItemResponse:
    branch: str
    supplier_name: str
    pending_count: int

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "supplier_name": self.supplier_name,
            "pending_count": self.pending_count,
        }


@dataclass
class InspecoesEntradaPendentesFornecedorResponse:
    branch: str
    items: list[InspecoesEntradaPendenteFornecedorItemResponse]
    total_suppliers: int
    total_pending: int

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "items": [item.to_dict() for item in self.items],
            "total_suppliers": self.total_suppliers,
            "total_pending": self.total_pending,
        }
