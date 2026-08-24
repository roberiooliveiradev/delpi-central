# app/tests/test_usage_tracking_purge_service.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.services.usage_tracking_purge_service import purge_usage_tracking_data


@patch("app.application.services.usage_tracking_purge_service.is_user_presence_enabled", return_value=False)
@patch("app.application.services.usage_tracking_purge_service.is_app_usage_enabled", return_value=False)
@patch(
    "app.infrastructure.persistence.sqlalchemy.usage_session_repository.SqlAlchemyUsageSessionRepository"
)
@patch("app.application.services.usage_tracking_purge_service.SqlAlchemyAppUsageRepository")
def test_purge_usage_tracking_data_deletes_events_and_sessions(
    mock_app_repo_cls,
    mock_session_repo_cls,
    _mock_app_enabled,
    _mock_presence_enabled,
):
    user_id = uuid4()
    mock_app_repo = MagicMock()
    mock_app_repo.delete_events_for_user.return_value = 5
    mock_app_repo_cls.return_value = mock_app_repo

    mock_session_repo = MagicMock()
    mock_session_repo_cls.return_value = mock_session_repo

    uow = MagicMock()
    deleted = purge_usage_tracking_data(uow, user_id=user_id)

    assert deleted == 5
    mock_app_repo.delete_events_for_user.assert_called_once_with(user_id=user_id)
    mock_session_repo.delete_sessions_for_user.assert_called_once_with(user_id=user_id)
