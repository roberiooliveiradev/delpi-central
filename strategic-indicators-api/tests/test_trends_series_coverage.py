"""Cobertura da série temporal (months vs period_scores materializados)."""

from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.get_trends_real_request import (
    GetStrategicIndicatorsTrendsRealRequest,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.use_cases.strategic_indicators.get_trends_real_use_case import (
    GetStrategicIndicatorsTrendsRealUseCase,
)
from si_app.config import settings
from si_app.interface.http.routes import strategic_indicators_routes as routes


def _period(competence: str) -> ResolvedPeriod:
    year, month = competence.split("-")
    return ResolvedPeriod(
        competence=competence,
        start_date=f"01-{month}-{year}",
        end_date=f"28-{month}-{year}",
    )


def _snapshot(competence: str, igd: float = 8.0) -> StrategicIndicatorsPeriodSnapshot:
    period = _period(competence)
    return StrategicIndicatorsPeriodSnapshot(
        period=period,
        measurements=[],
        measurement_errors=[],
        calculated_indicators=[],
        calculated_departments=[],
        igd=igd,
        igd_exact=igd,
        classification="alto",
    )


def test_refresh_trends_months_default_is_six() -> None:
    assert settings.SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS == 6


def test_tree_load_job_months_default_is_six() -> None:
    import inspect

    signature = inspect.signature(routes.create_departments_tree_load_job)
    months_param = signature.parameters["months"]
    assert months_param.default.default == 6


def test_build_response_marks_missing_competences_when_series_partial() -> None:
    use_case = GetStrategicIndicatorsTrendsRealUseCase(snapshot_service=MagicMock())
    requested = [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
    ]
    snapshots = [
        _snapshot("2026-03", 6.4),
        _snapshot("2026-04", 8.0),
        _snapshot("2026-05", 8.25),
        _snapshot("2026-06", 8.35),
    ]

    response = use_case.build_response_from_snapshots(
        snapshots,
        months_requested=6,
        competences_requested=requested,
    )

    assert response["months_requested"] == 6
    assert response["competences_requested"] == requested
    assert response["competences_returned"] == [
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
    ]
    assert response["missing_competences"] == ["2026-01", "2026-02"]
    assert len(response["igd_series"]) == 4
    assert response["partial_success"] is True


def test_execute_passes_coverage_from_requested_window() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_series_snapshot_optimized.return_value = [
        _snapshot("2026-04"),
        _snapshot("2026-05"),
        _snapshot("2026-06"),
    ]
    use_case = GetStrategicIndicatorsTrendsRealUseCase(
        snapshot_service=snapshot_service,
    )

    response = use_case.execute(
        GetStrategicIndicatorsTrendsRealRequest(
            competence="2026-06",
            months=6,
        )
    )

    assert response["months_requested"] == 6
    assert response["competences_requested"] == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
    ]
    assert response["missing_competences"] == ["2026-01", "2026-02", "2026-03"]
    assert snapshot_service.get_series_snapshot_optimized.call_args.kwargs[
        "prefer_materialized_only"
    ] is True


def test_presentation_trends_parity_with_trends_use_case() -> None:
    from si_app.application.use_cases.strategic_indicators.get_presentation_use_case import (
        GetStrategicIndicatorsPresentationUseCase,
    )

    snapshots = [
        _snapshot("2026-04", 7.1),
        _snapshot("2026-05", 7.5),
        _snapshot("2026-06", 8.0),
    ]
    snapshot_service = MagicMock()
    snapshot_service.get_series_snapshot_optimized.return_value = snapshots

    trends_uc = GetStrategicIndicatorsTrendsRealUseCase(
        snapshot_service=snapshot_service,
    )
    presentation_uc = GetStrategicIndicatorsPresentationUseCase(
        snapshot_service=snapshot_service,
        alerts_summary_port=MagicMock(),
        calculator=MagicMock(),
    )

    trends = trends_uc.execute(
        GetStrategicIndicatorsTrendsRealRequest(competence="2026-06", months=6)
    )
    presentation_trends = presentation_uc._build_trends(
        competence="2026-06",
        months=6,
        branch=None,
    )

    assert trends["igd_series"] == presentation_trends["igd_series"]
    assert trends["missing_competences"] == presentation_trends["missing_competences"]
    assert trends["months_requested"] == presentation_trends["months_requested"]
    assert (
        snapshot_service.get_series_snapshot_optimized.call_args_list[-1].kwargs[
            "prefer_materialized_only"
        ]
        is True
    )
