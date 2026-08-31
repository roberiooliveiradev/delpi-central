"""period_scores: catalog_hash igual + computed_at velho → miss."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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


def _closed_july() -> ResolvedPeriod:
    return ResolvedPeriod(
        competence="2026-07",
        start_date="01-07-2026",
        end_date="31-07-2026",
    )


def _service() -> StrategicIndicatorsSnapshotService:
    return StrategicIndicatorsSnapshotService(
        measurements_port=MagicMock(),
        calculator=MagicMock(),
        departments_catalog_repository=MagicMock(
            list_departments_catalog=MagicMock(return_value=[])
        ),
        resolved_indicators_catalog_repository=MagicMock(),
        period_scores_repository=MagicMock(),
    )


def test_cache_rejects_when_computed_at_older_than_max_age() -> None:
    period = _closed_july()
    snapshot = MagicMock()
    snapshot.period = period
    entry = PeriodScoresCacheEntry(
        snapshot=snapshot,
        version_number=1,
        is_clean=True,
        catalog_inputs_hash="abc123",
        computed_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    service = _service()

    with (
        patch.object(service, "_resolve_catalog_fingerprint", return_value="abc123"),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.period_extends_beyond_today",
            return_value=False,
        ),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.settings"
        ) as mock_settings,
    ):
        mock_settings.SI_PERIOD_SCORES_MAX_AGE_SECONDS = 3600
        assert (
            service._period_scores_cache_is_current(
                entry=entry,
                period=period,
                department_id=None,
                branch="01",
            )
            is False
        )


def test_cache_accepts_when_computed_at_within_max_age() -> None:
    period = _closed_july()
    snapshot = MagicMock()
    snapshot.period = period
    entry = PeriodScoresCacheEntry(
        snapshot=snapshot,
        version_number=1,
        is_clean=True,
        catalog_inputs_hash="abc123",
        computed_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    service = _service()

    with (
        patch.object(service, "_resolve_catalog_fingerprint", return_value="abc123"),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.period_extends_beyond_today",
            return_value=False,
        ),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.settings"
        ) as mock_settings,
    ):
        mock_settings.SI_PERIOD_SCORES_MAX_AGE_SECONDS = 3600
        assert (
            service._period_scores_cache_is_current(
                entry=entry,
                period=period,
                department_id=None,
                branch="01",
            )
            is True
        )


def test_cache_rejects_when_computed_at_missing_and_max_age_enabled() -> None:
    period = _closed_july()
    snapshot = MagicMock()
    snapshot.period = period
    entry = PeriodScoresCacheEntry(
        snapshot=snapshot,
        version_number=1,
        is_clean=True,
        catalog_inputs_hash="abc123",
        computed_at=None,
    )
    service = _service()

    with (
        patch.object(service, "_resolve_catalog_fingerprint", return_value="abc123"),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.period_extends_beyond_today",
            return_value=False,
        ),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.settings"
        ) as mock_settings,
    ):
        mock_settings.SI_PERIOD_SCORES_MAX_AGE_SECONDS = 3600
        assert (
            service._period_scores_cache_is_current(
                entry=entry,
                period=period,
                department_id=None,
                branch=None,
            )
            is False
        )


def test_cache_skips_max_age_when_disabled() -> None:
    period = _closed_july()
    snapshot = MagicMock()
    snapshot.period = period
    entry = PeriodScoresCacheEntry(
        snapshot=snapshot,
        version_number=1,
        is_clean=True,
        catalog_inputs_hash="abc123",
        computed_at=None,
    )
    service = _service()

    with (
        patch.object(service, "_resolve_catalog_fingerprint", return_value="abc123"),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.period_extends_beyond_today",
            return_value=False,
        ),
        patch(
            "si_app.application.services.strategic_indicators."
            "strategic_indicators_snapshot_service.settings"
        ) as mock_settings,
    ):
        mock_settings.SI_PERIOD_SCORES_MAX_AGE_SECONDS = 0
        assert (
            service._period_scores_cache_is_current(
                entry=entry,
                period=period,
                department_id=None,
                branch=None,
            )
            is True
        )
