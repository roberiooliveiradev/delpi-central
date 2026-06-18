from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesEntradaPendenteItemResponse:
    branch: str
    received_date: str | None
    received_time: str | None
    invoice_number: str
    supplier_code: str
    supplier_store: str
    supplier_name: str
    product_code: str
    product_description: str | None
    quantity: float
    unit: str
    status_code: str
    inspection_status: str

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "received_date": self.received_date,
            "received_time": self.received_time,
            "invoice_number": self.invoice_number,
            "supplier_code": self.supplier_code,
            "supplier_store": self.supplier_store,
            "supplier_name": self.supplier_name,
            "product_code": self.product_code,
            "product_description": self.product_description,
            "quantity": self.quantity,
            "unit": self.unit,
            "status_code": self.status_code,
            "inspection_status": self.inspection_status,
        }


@dataclass
class InspecoesEntradaPendentesPagination:
    page: int
    page_size: int
    total: int
    total_pages: int

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_pages": self.total_pages,
        }


@dataclass
class InspecoesEntradaPendentesResponse:
    branch: str
    items: list[InspecoesEntradaPendenteItemResponse]
    pagination: InspecoesEntradaPendentesPagination

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "items": [item.to_dict() for item in self.items],
            "pagination": self.pagination.to_dict(),
        }
