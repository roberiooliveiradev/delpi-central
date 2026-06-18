from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_filters import (
    InspecoesEntradaHistoricoFilters,
)
from app.application.dto.inspecoes_entrada.inspecoes_entrada_pendentes_response import (
    InspecoesEntradaPendentesPagination,
)


@dataclass
class InspecoesEntradaHistoricoItemResponse:
    branch: str
    inspection_id: str
    received_date: str | None
    received_time: str | None
    report_date: str | None
    report_time: str | None
    invoice_number: str
    invoice_series: str
    invoice_item: str
    supplier_code: str
    supplier_store: str
    supplier_name: str
    product_code: str
    product_description: str | None
    lot: str
    supplier_lot: str
    quantity: float
    unit: str
    status_code: str
    inspection_status: str
    result: str
    report_code: str
    approved_quantity: float | None
    rejected_quantity: float | None
    report_justification: str
    inspector_registration: str
    inspector_name: str
    inspector_login: str
    tests_count: int
    failed_tests_count: int
    is_approved: bool
    is_rejected: bool

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "inspection_id": self.inspection_id,
            "received_date": self.received_date,
            "received_time": self.received_time,
            "report_date": self.report_date,
            "report_time": self.report_time,
            "invoice_number": self.invoice_number,
            "invoice_series": self.invoice_series,
            "invoice_item": self.invoice_item,
            "supplier_code": self.supplier_code,
            "supplier_store": self.supplier_store,
            "supplier_name": self.supplier_name,
            "product_code": self.product_code,
            "product_description": self.product_description,
            "lot": self.lot,
            "supplier_lot": self.supplier_lot,
            "quantity": self.quantity,
            "unit": self.unit,
            "status_code": self.status_code,
            "inspection_status": self.inspection_status,
            "result": self.result,
            "report_code": self.report_code,
            "approved_quantity": self.approved_quantity,
            "rejected_quantity": self.rejected_quantity,
            "report_justification": self.report_justification,
            "inspector_registration": self.inspector_registration,
            "inspector_name": self.inspector_name,
            "inspector_login": self.inspector_login,
            "tests_count": self.tests_count,
            "failed_tests_count": self.failed_tests_count,
            "is_approved": self.is_approved,
            "is_rejected": self.is_rejected,
        }


@dataclass
class InspecoesEntradaHistoricoResponse:
    branch: str
    items: list[InspecoesEntradaHistoricoItemResponse]
    pagination: InspecoesEntradaPendentesPagination
    filters: InspecoesEntradaHistoricoFilters

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "items": [item.to_dict() for item in self.items],
            "pagination": self.pagination.to_dict(),
            "filters": self.filters.to_dict(),
        }
