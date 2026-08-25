from app.domain.production.eficiencia_fabril_efficiency_by_work_center import (
    aggregate_efficiency_by_work_center,
    average_efficiency_across_work_centers,
    headline_work_center_efficiency_pct,
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
    assert average_efficiency_across_work_centers(rows) == 77.5
    assert headline_work_center_efficiency_pct(items) == 77.5


def test_headline_efficiency_is_mean_of_ct_averages_not_appointments() -> None:
    items = [
        {"centro_trabalho": "CT-A", "status_registro": "OK", "eficiencia_percentual": 100.0},
        {"centro_trabalho": "CT-A", "status_registro": "OK", "eficiencia_percentual": 100.0},
        {"centro_trabalho": "CT-A", "status_registro": "OK", "eficiencia_percentual": 100.0},
        {"centro_trabalho": "CT-B", "status_registro": "OK", "eficiencia_percentual": 80.0},
    ]
    # Média dos apontamentos seria 95; média dos CTs (100 e 80) é 90.
    assert headline_work_center_efficiency_pct(items) == 90.0


def test_headline_efficiency_matches_shift_comparison_reference() -> None:
    # Recorte de referência (24/08 + turno 1): média dos CTs = 93,77%.
    # CT-A com 2 apontamentos a 90% não puxa o KPI como se fossem 2 CTs.
    items = [
        {"centro_trabalho": "CT-A", "status_registro": "OK", "eficiencia_percentual": 90.0},
        {"centro_trabalho": "CT-A", "status_registro": "OK", "eficiencia_percentual": 90.0},
        {"centro_trabalho": "CT-B", "status_registro": "OK", "eficiencia_percentual": 97.54},
    ]
    assert headline_work_center_efficiency_pct(items) == 93.77
    appointment_mean = (90.0 + 90.0 + 97.54) / 3
    assert round(appointment_mean, 2) == 92.51


def test_average_across_work_centers_skips_placeholder_and_empty() -> None:
    assert (
        average_efficiency_across_work_centers(
            [
                {"work_center": "—", "efficiency_pct": 10.0},
                {"work_center": "  ", "efficiency_pct": 20.0},
                {"work_center": "CT-01C", "efficiency_pct": 93.77},
            ]
        )
        == 93.77
    )


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
