from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    PeriodScoresCacheEntry,
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    resolve_period,
)


def test_load_stored_period_snapshot_skips_reconcile_when_hash_matches() -> None:
    period = resolve_period(
        competence="2026-05",
        start_date=None,
        end_date=None,
    )
    stored = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    stored.period = period

    service = StrategicIndicatorsSnapshotService(
        departments_catalog_repository=MagicMock(),
        resolved_indicators_catalog_repository=MagicMock(),
        measurements_port=MagicMock(),
        calculator=MagicMock(),
        period_scores_repository=MagicMock(),
    )

    service._period_scores_cache_is_current = MagicMock(return_value=True)  # type: ignore[method-assign]
    service._reconcile_stored_period_snapshot = MagicMock()  # type: ignore[method-assign]

    entry = PeriodScoresCacheEntry(
        snapshot=stored,
        catalog_inputs_hash="abc123",
    )
    service._period_scores_repository.get_period_snapshot.return_value = entry

    result = service._load_stored_period_snapshot(
        period=period,
        department_id=None,
        branch=None,
    )

    assert result is stored
    service._reconcile_stored_period_snapshot.assert_not_called()


def test_partial_comparative_computes_only_missing_period() -> None:
    period_current = resolve_period(
        competence="2026-05",
        start_date=None,
        end_date=None,
    )
    period_previous = resolve_period(
        competence="2026-04",
        start_date=None,
        end_date=None,
    )
    stored_current = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    stored_current.period = period_current

    service = StrategicIndicatorsSnapshotService(
        departments_catalog_repository=MagicMock(),
        resolved_indicators_catalog_repository=MagicMock(),
        measurements_port=MagicMock(),
        calculator=MagicMock(),
        period_scores_repository=MagicMock(),
    )

    computed_previous = MagicMock(spec=StrategicIndicatorsPeriodSnapshot)
    service._compute_and_persist_period = MagicMock(return_value=computed_previous)  # type: ignore[method-assign]
    service.get_catalog_snapshot = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(indicators_catalog=[], departments_catalog=[], goals_by_department={})
    )

    comparative = service._get_comparative_with_partial_stored(
        started=0.0,
        current_period=period_current,
        previous_period_resolved=period_previous,
        stored_current=stored_current,
        stored_previous=None,
        department_id=None,
        branch=None,
    )

    service._compute_and_persist_period.assert_called_once()
    call_kwargs = service._compute_and_persist_period.call_args.kwargs
    assert call_kwargs["period"].competence == "2026-04"
    assert comparative.current is stored_current
    assert comparative.previous is computed_previous
