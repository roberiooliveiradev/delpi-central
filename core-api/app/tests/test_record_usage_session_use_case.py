# app/tests/test_record_usage_session_use_case.py

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.use_cases.admin.record_usage_session_use_case import (
    RecordUsageSessionUseCase,
)


@patch(
    "app.application.use_cases.admin.record_usage_session_use_case.SqlAlchemyUsageSessionRepository"
)
@patch(
    "app.application.use_cases.admin.record_usage_session_use_case.user_has_usage_tracking_consent",
    return_value=True,
)
def test_record_usage_session_persists_segment(mock_consent, mock_repo_cls):
    mock_repo = MagicMock()
    mock_repo_cls.return_value = mock_repo
    uow = MagicMock()
    use_case = RecordUsageSessionUseCase(uow)

    user_id = str(uuid4())
    started = datetime.utcnow() - timedelta(minutes=5)
    ended = datetime.utcnow()

    recorded = use_case.execute(
        user_id=user_id,
        app_id="commercial",
        route_path="/apps/commercial",
        started_at=started,
        ended_at=ended,
        source="socket_close",
        socket_session_id="sid-1",
    )

    assert recorded is True
    mock_repo.record_session.assert_called_once()
    kwargs = mock_repo.record_session.call_args.kwargs
    assert kwargs["app_id"] == "commercial"
    assert kwargs["duration_seconds"] == 300


@patch(
    "app.application.use_cases.admin.record_usage_session_use_case.SqlAlchemyUsageSessionRepository"
)
@patch(
    "app.application.use_cases.admin.record_usage_session_use_case.user_has_usage_tracking_consent",
    return_value=False,
)
def test_record_usage_session_skips_without_consent(mock_consent, mock_repo_cls):
    mock_repo = MagicMock()
    mock_repo_cls.return_value = mock_repo
    uow = MagicMock()
    use_case = RecordUsageSessionUseCase(uow)
    now = datetime.utcnow()

    recorded = use_case.execute(
        user_id=str(uuid4()),
        app_id="commercial",
        route_path=None,
        started_at=now - timedelta(minutes=1),
        ended_at=now,
        source="socket_close",
    )

    assert recorded is False
    mock_repo.record_session.assert_not_called()
