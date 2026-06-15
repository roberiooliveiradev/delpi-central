from unittest.mock import MagicMock

from app.application.dto.production.get_production_otd_request import (
    GetProductionOtdRequest,
)
from app.application.models.page import Page
from app.application.use_cases.production.get_production_otd_use_case import (
    GetProductionOtdUseCase,
)
from app.domain.entities.production.on_time_delivery import OnTimeDelivery


def test_get_production_otd_use_case_returns_summary_and_orders():
    repository = MagicMock()
    repository.get_on_time_delivery.return_value = OnTimeDelivery(
        branch="01",
        total_ops_finished=10,
        on_time_ops=8,
        late_ops=2,
        on_time_delivery_pct=80.0,
    )
    repository.list_production_orders_otd.return_value = Page(
        items=[
            {
                "branch": "01",
                "order_number": "000001",
                "status": "late",
            }
        ],
        total=1,
        page=1,
        page_size=20,
    )

    use_case = GetProductionOtdUseCase(repository)
    result = use_case.execute(
        GetProductionOtdRequest(
            branch="01",
            start_date="2024-01-01",
            end_date="2024-01-31",
            page=1,
            page_size=20,
        )
    )

    assert result["summary"]["total_ops_finished"] == 10
    assert result["summary"]["on_time_ops"] == 8
    assert result["summary"]["late_ops"] == 2
    assert result["summary"]["on_time_delivery_pct"] == 80.0
    assert result["summary"]["late_percentage"] == 20.0
    assert result["orders"]["total"] == 1
    assert result["orders"]["items"][0]["status"] == "late"
