from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.dto.eficiencia_fabril.eficiencia_fabril_dashboard_response import (
    EficienciaFabrilCharts,
    EficienciaFabrilDashboardItem,
    EficienciaFabrilDashboardResponse,
    EficienciaFabrilPagination,
    EficienciaFabrilSummary,
)
from app.application.use_cases.eficiencia_fabril.get_eficiencia_fabril_dashboard_use_case import (
    GetEficienciaFabrilDashboardUseCase,
)
from app.infrastructure.persistence.totvs.eficiencia_fabril.eficiencia_fabril_query_settings import (
    EficienciaFabrilQuerySettings,
)


def _dashboard_response() -> EficienciaFabrilDashboardResponse:
    return EficienciaFabrilDashboardResponse(
        summary=EficienciaFabrilSummary(
            weighted_efficiency_pct=73.77,
            total_mod_result=-100.0,
            total_mod_profit=50.0,
            total_mod_loss=150.0,
            total_hours_gained_lost=-2.5,
            appointment_count=10,
            invalid_record_count=2,
        ),
        charts=EficienciaFabrilCharts(
            efficiency_by_day=[{"date": "2026-05-27", "efficiency_pct": 80.0}],
            mod_result_by_day=[{"date": "2026-05-27", "net_result": -10.0}],
            efficiency_by_operator=[
                {"operator_name": "Operador A", "efficiency_pct": 90.0}
            ],
            hours_by_work_center=[{"work_center": "CT-01A", "real_hours": 5.0}],
        ),
        items=[
            EficienciaFabrilDashboardItem(
                filial="02",
                op="10312301005",
                nome_operador="Operador A",
                data_producao="2026-05-27",
                eficiencia_percentual=51.36,
                status_registro="OK",
            )
        ],
        pagination=EficienciaFabrilPagination(page=1, page_size=50, total=1),
    )


def test_dashboard_use_case_returns_repository_payload() -> None:
    repository = MagicMock()
    repository.get_dashboard.return_value = _dashboard_response()

    use_case = GetEficienciaFabrilDashboardUseCase(repository)
    result = use_case.execute(
        date_start="2026-05-01",
        date_end="2026-05-27",
        branch="02",
        page=1,
        page_size=25,
    )

    repository.get_dashboard.assert_called_once()
    request = repository.get_dashboard.call_args[0][0]
    assert request.date_start == date(2026, 5, 1)
    assert request.date_end == date(2026, 5, 27)
    assert request.branch == "02"
    assert request.page_size == 25
    assert result.summary.appointment_count == 10
    assert result.pagination.total == 1
    assert len(result.charts.efficiency_by_day) == 1


def test_dashboard_requires_date_range() -> None:
    use_case = GetEficienciaFabrilDashboardUseCase(MagicMock())

    with pytest.raises(ValueError, match="date_start"):
        use_case.execute(date_start=None, date_end="2026-05-27")

    with pytest.raises(ValueError, match="date_end"):
        use_case.execute(date_start="2026-05-01", date_end=None)


def test_dashboard_rejects_invalid_branch() -> None:
    use_case = GetEficienciaFabrilDashboardUseCase(
        MagicMock(),
        settings=EficienciaFabrilQuerySettings(branches=["01", "02"]),
    )

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(
            date_start="2026-05-01",
            date_end="2026-05-27",
            branch="99",
        )


def test_dashboard_rejects_long_date_range() -> None:
    use_case = GetEficienciaFabrilDashboardUseCase(
        MagicMock(),
        settings=EficienciaFabrilQuerySettings(max_date_range_days=30),
    )

    with pytest.raises(ValueError, match="Intervalo máximo"):
        use_case.execute(
            date_start="2025-01-01",
            date_end="2026-05-27",
        )
