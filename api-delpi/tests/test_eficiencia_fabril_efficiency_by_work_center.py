from app.domain.production.eficiencia_fabril_efficiency_by_work_center import (
    aggregate_efficiency_by_work_center,
)


def test_aggregate_efficiency_by_work_center_matches_plugin_rules() -> None:
    items = [
        {
            "centro_trabalho": "CT-01C",
            "status_registro": "OK",
            "eficiencia_percentual": 100.0,
        },
        {
            "centro_trabalho": "CT-01C",
            "status_registro": "OK",
            "eficiencia_percentual": 50.0,
        },
        # outlier — fora da média
        {
            "centro_trabalho": "CT-01C",
            "status_registro": "OK",
            "eficiencia_percentual": 250.0,
        },
        # não OK — ignorado
        {
            "centro_trabalho": "CT-01C",
            "status_registro": "ERRO",
            "eficiencia_percentual": 10.0,
        },
        {
            "centro_trabalho": "CT-02A",
            "status_registro": "OK",
            "eficiencia_percentual": 80.0,
        },
    ]

    rows = aggregate_efficiency_by_work_center(items)
    assert rows == [
        {"work_center": "CT-01C", "efficiency_pct": 75.0, "appointment_count": 2},
        {"work_center": "CT-02A", "efficiency_pct": 80.0, "appointment_count": 1},
    ]


def test_use_case_delegates_to_appointments_and_aggregates() -> None:
    from unittest.mock import MagicMock

    from app.application.use_cases.eficiencia_fabril.get_eficiencia_fabril_efficiency_by_work_center_use_case import (
        GetEficienciaFabrilEfficiencyByWorkCenterUseCase,
    )

    appointments = MagicMock()
    appointments.execute.return_value = [
        {
            "centro_trabalho": "CT-01C",
            "status_registro": "OK",
            "eficiencia_percentual": 75.71,
        }
    ]
    use_case = GetEficienciaFabrilEfficiencyByWorkCenterUseCase(appointments)
    result = use_case.execute(
        date_start="2026-08-01",
        date_end="2026-08-07",
        branch="02",
        shift="1",
    )
    appointments.execute.assert_called_once_with(
        date_start="2026-08-01",
        date_end="2026-08-07",
        branch="02",
        op=None,
        employee=None,
        work_center=None,
        status_ok_only=True,
        shift="1",
    )
    assert result[0]["work_center"] == "CT-01C"
    assert result[0]["efficiency_pct"] == 75.71
