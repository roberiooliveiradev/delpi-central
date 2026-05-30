# app/tests/test_record_integrated_app_usage_use_case.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.use_cases.admin.record_integrated_app_usage_use_case import (
    RecordIntegratedAppUsageResult,
    RecordIntegratedAppUsageUseCase,
)
from app.domain.ports.consent_repository_port import ConsentDTO


def _consent(granted: bool) -> ConsentDTO:
    return ConsentDTO(
        id=uuid4(),
        user_id=uuid4(),
        purpose="usage_tracking",
        granted=granted,
        granted_at=None,
        revoked_at=None,
    )


def test_execute_skips_without_usage_tracking_consent():
    user_id = uuid4()
    uow = MagicMock()
    uow.consents.get_by_user_and_purpose.return_value = _consent(False)
    uow.session.query.return_value.filter.return_value.first.return_value = MagicMock()

    use_case = RecordIntegratedAppUsageUseCase(uow)

    with patch(
        "app.application.use_cases.admin.record_integrated_app_usage_use_case.RecordAppUsageUseCase"
    ) as record_cls:
        result = use_case.execute(
            app_id="api-delpi",
            user_id=str(user_id),
            route_path="/commercial",
            caller_app_id="minha-delpi-chat",
        )

    assert result == RecordIntegratedAppUsageResult.SKIPPED_CONSENT
    record_cls.return_value.execute.assert_not_called()


def test_execute_records_with_consent_and_caller_app():
    user_id = uuid4()
    uow = MagicMock()
    uow.consents.get_by_user_and_purpose.return_value = _consent(True)
    uow.session.query.return_value.filter.return_value.first.return_value = MagicMock()

    use_case = RecordIntegratedAppUsageUseCase(uow)

    with patch(
        "app.application.use_cases.admin.record_integrated_app_usage_use_case.RecordAppUsageUseCase"
    ) as record_cls:
        result = use_case.execute(
            app_id="api-delpi",
            user_id=str(user_id),
            route_path="/commercial",
            caller_app_id="minha-delpi-chat",
        )

    assert result == RecordIntegratedAppUsageResult.RECORDED
    record_cls.return_value.execute.assert_called_once_with(
        user_id=str(user_id),
        session_id=f"integration:api-delpi:{user_id}",
        app_id="api-delpi",
        route_path="/commercial",
        caller_app_id="minha-delpi-chat",
        source="integration",
    )
