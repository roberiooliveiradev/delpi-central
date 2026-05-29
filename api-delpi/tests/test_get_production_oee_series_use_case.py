from unittest.mock import MagicMock

from app.application.dto.production.production_oee_series_request import (
    ProductionOeeSeriesRequest,
)
from app.application.use_cases.production.get_production_oee_series_use_case import (
    GetProductionOeeSeriesUseCase,
)
from app.domain.entities.production.overall_equipment_effectiveness import (
    OverallEquipmentEffectiveness,
)


def test_production_oee_series_returns_points_per_bucket() -> None:
    repository = MagicMock()

    def fake_oee(request):
        value = 80.0 if request.branch == "01" else 70.0
        return OverallEquipmentEffectiveness(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            oee_pct=value,
        )

    repository.get_overall_equipment_effectiveness.side_effect = fake_oee

    use_case = GetProductionOeeSeriesUseCase(repository)
    result = use_case.execute(
        ProductionOeeSeriesRequest(
            granularity="month",
            date_start="2026-05-01",
            date_end="2026-05-31",
        )
    )

    assert result.points
    assert result.points[0].oee_filial_01 == 80.0
    assert result.points[0].oee_filial_02 == 70.0
    assert result.branch is None


def test_production_oee_series_filters_single_branch() -> None:
    repository = MagicMock()
    repository.get_overall_equipment_effectiveness.return_value = (
        OverallEquipmentEffectiveness(
            branch="02",
            start_date="2026-05-01",
            end_date="2026-05-31",
            oee_pct=65.5,
        )
    )

    use_case = GetProductionOeeSeriesUseCase(repository)
    result = use_case.execute(
        ProductionOeeSeriesRequest(
            granularity="month",
            date_start="2026-05-01",
            date_end="2026-05-31",
            branch="02",
        )
    )

    assert result.branch == "02"
    assert result.points[0].oee_filial_01 is None
    assert result.points[0].oee_filial_02 == 65.5
