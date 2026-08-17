"""Mat-only deve servir mês corrente materializado (ainda aberto)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    PeriodScoresCacheEntry,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)


def _open_august() -> ResolvedPeriod:
    return ResolvedPeriod(
        competence="2026-08",
        start_date="01-08-2026",
        end_date="31-08-2026",
    )


def _service_with_entry(entry: PeriodScoresCacheEntry) -> StrategicIndicatorsSnapshotService:
    repo = MagicMock()
    repo.list_period_snapshots.return_value = {"2026-08": entry}
    return StrategicIndicatorsSnapshotService(
        measurements_port=MagicMock(),
        calculator=MagicMock(),
        departments_catalog_repository=MagicMock(
            list_departments_catalog=MagicMock(return_value=[])
        ),
        resolved_indicators_catalog_repository=MagicMock(),
        period_scores_repository=repo,
    )


def test_cache_rejects_open_month_unless_allow_open_month() -> None:
    period = _open_august()
    snapshot = MagicMock()
    snapshot.period = period
    entry = PeriodScoresCacheEntry(
        snapshot=snapshot,
        version_number=1,
        is_clean=True,
        catalog_inputs_hash="abc123",
    )
    service = _service_with_entry(entry)

    with (
        patch.object(service, "_resolve_catalog_fingerprint", return_value="abc123"),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.period_extends_beyond_today",
            return_value=True,
        ),
    ):
        assert (
            service._period_scores_cache_is_current(
                entry=entry,
                period=period,
                department_id=None,
                branch=None,
                allow_open_month=False,
            )
            is False
        )
        assert (
            service._period_scores_cache_is_current(
                entry=entry,
                period=period,
                department_id=None,
                branch=None,
                allow_open_month=True,
            )
            is True
        )


def test_mat_only_series_serves_open_month_from_period_scores() -> None:
    """Regressão Tendências: mês aberto existia no banco mas virava missing_competences."""
    period = _open_august()
    snapshot = MagicMock()
    snapshot.period = period
    snapshot.igd = 6.59
    snapshot.measurement_errors = []
    entry = PeriodScoresCacheEntry(
        snapshot=snapshot,
        version_number=1,
        is_clean=True,
        catalog_inputs_hash="abc123",
    )
    service = _service_with_entry(entry)

    with (
        patch.object(service, "_resolve_catalog_fingerprint", return_value="abc123"),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.settings"
        ) as settings_mock,
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.period_extends_beyond_today",
            return_value=True,
        ),
    ):
        settings_mock.SI_PERIOD_SCORES_ENABLED = True
        result = service.get_series_snapshot_optimized(
            periods=[period],
            prefer_materialized_only=True,
        )

    assert len(result) == 1
    assert result[0].igd == 6.59
