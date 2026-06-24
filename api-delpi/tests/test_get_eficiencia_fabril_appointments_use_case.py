from unittest.mock import MagicMock, patch

import pytest

from app.application.dto.eficiencia_fabril.eficiencia_fabril_dashboard_response import (
    EficienciaFabrilDashboardItem,
)
from app.application.use_cases.eficiencia_fabril.get_eficiencia_fabril_appointments_use_case import (
    GetEficienciaFabrilAppointmentsUseCase,
)
from app.composition.query_cache_composer import reset_query_cache_for_tests


def _sample_item() -> EficienciaFabrilDashboardItem:
    return EficienciaFabrilDashboardItem(
        appointment_id=123,
        filial="01",
        op="10312301005",
        nome_operador="Operador A",
        data_producao="2026-05-27",
        eficiencia_percentual=51.36,
        status_registro="OK",
    )


def test_execute_caches_appointments_without_second_repository_call() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_appointments.return_value = [_sample_item()]

    use_case = GetEficienciaFabrilAppointmentsUseCase(repository)

    first = use_case.execute(
        date_start="2026-05-01",
        date_end="2026-05-31",
        branch="01",
    )
    second = use_case.execute(
        date_start="2026-05-01",
        date_end="2026-05-31",
        branch="01",
    )

    assert first[0]["appointment_id"] == 123
    assert second == first
    repository.get_appointments.assert_called_once()


def test_execute_returns_cached_response_without_repository_call() -> None:
    repository = MagicMock()
    use_case = GetEficienciaFabrilAppointmentsUseCase(repository)

    cached = [{"appointment_id": 99, "filial": "01", "op": "1"}]

    with patch(
        "app.application.use_cases.eficiencia_fabril.get_eficiencia_fabril_appointments_use_case.get_cached_eficiencia_fabril_appointments",
        return_value=cached,
    ):
        result = use_case.execute(
            date_start="2026-05-01",
            date_end="2026-05-31",
        )

    assert result == cached
    repository.get_appointments.assert_not_called()


def test_execute_requires_date_range() -> None:
    use_case = GetEficienciaFabrilAppointmentsUseCase(MagicMock())

    with pytest.raises(ValueError, match="date_start"):
        use_case.execute(date_start=None, date_end="2026-05-31")
