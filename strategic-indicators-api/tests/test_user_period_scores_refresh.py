from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from si_app.application.services.strategic_indicators.user_period_scores_refresh import (
    is_period_scores_refresh_in_progress,
)


def test_refresh_in_progress_when_started_after_completed() -> None:
    now = datetime.now(timezone.utc)
    repo = MagicMock()
    repo.get_status.return_value = {
        "last_started_at": now,
        "last_completed_at": now - timedelta(minutes=5),
        "last_error": None,
    }
    with patch(
        "si_app.application.services.strategic_indicators.user_period_scores_refresh.PostgresStrategicIndicatorsRefreshStateRepository",
        return_value=repo,
    ):
        assert is_period_scores_refresh_in_progress() is True


def test_refresh_not_in_progress_when_completed_after_started() -> None:
    now = datetime.now(timezone.utc)
    repo = MagicMock()
    repo.get_status.return_value = {
        "last_started_at": now - timedelta(minutes=5),
        "last_completed_at": now,
        "last_error": None,
    }
    with patch(
        "si_app.application.services.strategic_indicators.user_period_scores_refresh.PostgresStrategicIndicatorsRefreshStateRepository",
        return_value=repo,
    ):
        assert is_period_scores_refresh_in_progress() is False


def test_refresh_not_in_progress_when_last_error() -> None:
    now = datetime.now(timezone.utc)
    repo = MagicMock()
    repo.get_status.return_value = {
        "last_started_at": now,
        "last_completed_at": None,
        "last_error": "falhou",
    }
    with patch(
        "si_app.application.services.strategic_indicators.user_period_scores_refresh.PostgresStrategicIndicatorsRefreshStateRepository",
        return_value=repo,
    ):
        assert is_period_scores_refresh_in_progress() is False
