from unittest.mock import MagicMock

from app.application.dto.production.production_otd_series_request import (
    ProductionOtdSeriesRequest,
)
from app.application.use_cases.production.get_production_otd_series_use_case import (
    GetProductionOtdSeriesUseCase,
)
from app.domain.entities.production.on_time_delivery import OnTimeDelivery


def test_production_otd_series_returns_points_per_bucket() -> None:
    repository = MagicMock()

    def fake_otd(request):
        value = 88.0 if request.branch == "01" else 72.0
        return OnTimeDelivery(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            total_ops_finished=10,
            on_time_ops=8,
            late_ops=2,
            on_time_delivery_pct=value,
        )

    repository.get_on_time_delivery.side_effect = fake_otd

    use_case = GetProductionOtdSeriesUseCase(repository)
    result = use_case.execute(
        ProductionOtdSeriesRequest(
            granularity="month",
            date_start="2026-05-01",
            date_end="2026-05-31",
        )
    )

    assert result.points
    assert result.points[0].otd_filial_01 == 88.0
    assert result.points[0].otd_filial_02 == 72.0


def test_production_otd_series_treats_empty_otd_as_null() -> None:
    repository = MagicMock()
    repository.get_on_time_delivery.return_value = OnTimeDelivery(
        branch="01",
        start_date="2026-05-01",
        end_date="2026-05-01",
        total_ops_finished=0,
        on_time_ops=0,
        late_ops=0,
        on_time_delivery_pct="",
    )

    use_case = GetProductionOtdSeriesUseCase(repository)
    result = use_case.execute(
        ProductionOtdSeriesRequest(
            granularity="day",
            date_start="2026-05-01",
            date_end="2026-05-02",
        )
    )

    assert result.points[0].otd_filial_01 is None
    assert result.points[0].otd_filial_02 is None
