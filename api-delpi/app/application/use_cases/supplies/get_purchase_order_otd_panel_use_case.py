from __future__ import annotations

from app.application.dto.supplies.get_purchase_order_otd_panel_request import (
    GetPurchaseOrderOtdPanelRequest,
)
from app.application.dto.supplies.purchase_order_otd_request import PurchaseOrderOtdRequest
from app.domain.ports.supplies.purchase_order_otd_repository_port import (
    PurchaseOrderOtdRepositoryPort,
)
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL


class GetPurchaseOrderOtdPanelUseCase:
    def __init__(self, *, purchase_order_otd_repository: PurchaseOrderOtdRepositoryPort):
        self._repository = purchase_order_otd_repository

    def execute(self, request: GetPurchaseOrderOtdPanelRequest) -> dict:
        summary_request = PurchaseOrderOtdRequest(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        indicator = self._repository.get_purchase_order_otd(summary_request)
        lines_page = self._repository.list_purchase_order_otd_lines(request)

        total_lines = int(indicator.total_lines or 0)
        on_time_lines = int(indicator.on_time_lines or 0)
        late_lines = int(indicator.late_lines or 0)
        late_percentage = (
            round(late_lines * 100.0 / total_lines, 2) if total_lines > 0 else 0.0
        )

        return {
            "branch": request.branch or "consolidated",
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "product_type": PRODUCT_TYPE_RAW_MATERIAL,
            "summary": {
                "total_lines": total_lines,
                "on_time_lines": on_time_lines,
                "late_lines": late_lines,
                "purchase_order_otd_pct": indicator.purchase_order_otd_pct,
                "late_percentage": late_percentage,
            },
            "lines": lines_page.to_dict(),
        }
