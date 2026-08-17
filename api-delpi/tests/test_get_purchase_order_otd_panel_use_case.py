from unittest.mock import MagicMock

from app.application.dto.supplies.get_purchase_order_otd_panel_request import (
    GetPurchaseOrderOtdPanelRequest,
)
from app.application.models.page import Page
from app.application.use_cases.supplies.get_purchase_order_otd_panel_use_case import (
    GetPurchaseOrderOtdPanelUseCase,
)
from app.domain.entities.supplies.purchase_order_otd import PurchaseOrderOtd
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL


class _FakeRepo:
    def get_purchase_order_otd(self, request):
        return PurchaseOrderOtd(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            product_type=PRODUCT_TYPE_RAW_MATERIAL,
            total_lines=10,
            on_time_lines=8,
            late_lines=2,
            purchase_order_otd_pct=80.0,
        )

    def list_purchase_order_otd_lines(self, request):
        return Page(
            items=[{"order_number": "000001", "status": "late"}],
            total=1,
            page=request.page,
            page_size=request.page_size,
        )


def test_panel_use_case_returns_summary_and_lines() -> None:
    use_case = GetPurchaseOrderOtdPanelUseCase(
        purchase_order_otd_repository=_FakeRepo()
    )
    result = use_case.execute(
        GetPurchaseOrderOtdPanelRequest(
            branch="01",
            start_date="2026-07-01",
            end_date="2026-07-31",
            status="late",
        )
    )

    assert result["product_type"] == PRODUCT_TYPE_RAW_MATERIAL
    assert result["summary"]["purchase_order_otd_pct"] == 80.0
    assert result["summary"]["late_percentage"] == 20.0
    assert result["lines"]["total"] == 1
    assert result["lines"]["items"][0]["order_number"] == "000001"
