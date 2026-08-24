# app/tests/test_get_user_usage_statistics_use_case.py

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.admin.get_user_usage_statistics_use_case import (
    GetUserUsageStatisticsUseCase,
)
from app.domain.ports.user_repository_port import UserDTO


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def user_dto(user_id):
    return UserDTO(
        id=user_id,
        email="user@example.com",
        name="Maria Silva",
        active=True,
        is_superadmin=False,
        last_login_at=datetime(2026, 8, 20, 12, 0, 0),
        birth_date=None,
    )


@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.is_app_usage_enabled",
    return_value=True,
)
@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.user_has_usage_tracking_consent",
    return_value=True,
)
@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.SqlAlchemyEngagementRepository"
)
def test_execute_returns_user_usage_with_consent(
    mock_repo_cls,
    _mock_consent,
    _mock_tracking,
    user_id,
    user_dto,
):
    mock_repo = MagicMock()
    mock_repo_cls.return_value = mock_repo
    mock_repo.window_since.return_value = datetime(2026, 7, 25, 0, 0, 0)
    mock_repo.user_usage_summary.return_value = {
        "totalOpens": 12,
        "appsUsed": 3,
        "totalDurationSeconds": 3600,
        "portalDurationSeconds": 1200,
        "appDurationSeconds": 2400,
        "avgSessionSeconds": 600,
        "lastAppUsageAt": "2026-08-24T10:00:00Z",
    }
    mock_repo.user_opens_by_day.return_value = [{"date": "2026-08-24", "opens": 5}]
    mock_repo.user_duration_by_day.return_value = [
        {"date": "2026-08-24", "totalSeconds": 900}
    ]
    mock_repo.user_apps_by_opens.return_value = [{"id": "commercial", "name": "Comercial", "count": 5}]
    mock_repo.user_apps_by_duration.return_value = []
    mock_repo.user_routes_by_opens.return_value = []
    mock_repo.user_count_sessions_since.return_value = 4
    mock_repo.user_count_events_since.return_value = 12

    uow = MagicMock()
    uow.users.get_by_id.return_value = user_dto

    result = GetUserUsageStatisticsUseCase(uow).execute(
        user_id=user_id,
        period_days=30,
    )

    assert result["periodDays"] == 30
    assert result["user"]["email"] == "user@example.com"
    assert result["consent"]["granted"] is True
    assert result["summary"]["totalOpens"] == 12
    assert result["activity"]["opensSeries"][0]["opens"] == 5
    assert result["coverage"]["eventsInPeriod"] == 12


@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.is_app_usage_enabled",
    return_value=True,
)
@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.user_has_usage_tracking_consent",
    return_value=False,
)
@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.SqlAlchemyEngagementRepository"
)
def test_execute_returns_zeros_without_consent(
    mock_repo_cls,
    _mock_consent,
    _mock_tracking,
    user_id,
    user_dto,
):
    mock_repo_cls.return_value = MagicMock()
    uow = MagicMock()
    uow.users.get_by_id.return_value = user_dto

    result = GetUserUsageStatisticsUseCase(uow).execute(
        user_id=user_id,
        period_days=7,
    )

    assert result["consent"]["granted"] is False
    assert result["summary"]["totalOpens"] == 0
    assert result["activity"]["opensSeries"] == []
    assert result["coverage"]["eventsInPeriod"] == 0


def test_execute_raises_for_unknown_user(user_id):
    uow = MagicMock()
    uow.users.get_by_id.return_value = None

    with pytest.raises(LookupError, match="Usuário não encontrado"):
        GetUserUsageStatisticsUseCase(uow).execute(user_id=user_id, period_days=30)


def test_execute_rejects_invalid_period(user_id, user_dto):
    uow = MagicMock()
    uow.users.get_by_id.return_value = user_dto

    with pytest.raises(ValueError, match="periodDays inválido"):
        GetUserUsageStatisticsUseCase(uow).execute(user_id=user_id, period_days=14)
