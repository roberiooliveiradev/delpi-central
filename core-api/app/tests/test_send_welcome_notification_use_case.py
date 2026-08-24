# app/tests/test_send_welcome_notification_use_case.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.dto.notification_dispatch_response import NotificationDispatchResponse
from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.send_welcome_notification_use_case import (
    SendWelcomeNotificationUseCase,
)
from app.domain.notifications.notification_automation import SOURCE_APP_WELCOME_AUTOMATION


@pytest.fixture
def uow():
    mock = MagicMock()
    mock.notification_preferences = MagicMock()
    return mock


def test_execute_dispatches_welcome_via_automation_service(uow):
    user_id = str(uuid4())
    dispatch_id = str(uuid4())
    notification_id = str(uuid4())
    uow.notification_preferences.filter_user_ids_accepting_category.return_value = [
        user_id
    ]
    expected = NotificationDispatchResponse(
        dispatch_id=dispatch_id,
        status="completed",
        scheduled_at=None,
        created_count=1,
        notification_ids=[notification_id],
        recipient_count=1,
    )

    with patch(
        "app.application.use_cases.send_welcome_notification_use_case.AutomatedNotificationDispatchService"
    ) as service_cls:
        service_cls.return_value.dispatch.return_value = expected
        result = SendWelcomeNotificationUseCase(uow).execute(user_id)

    service_cls.return_value.dispatch.assert_called_once()
    request = service_cls.return_value.dispatch.call_args[0][0]
    assert request.source_app == SOURCE_APP_WELCOME_AUTOMATION
    assert request.user_ids == [user_id]
    assert result["createdCount"] == 1
    assert result["notificationIds"] == [notification_id]


def test_execute_skips_dispatch_when_category_is_muted(uow):
    user_id = str(uuid4())
    uow.notification_preferences.filter_user_ids_accepting_category.return_value = []

    with patch(
        "app.application.use_cases.send_welcome_notification_use_case.AutomatedNotificationDispatchService"
    ) as service_cls:
        result = SendWelcomeNotificationUseCase(uow).execute(user_id)

    service_cls.return_value.dispatch.assert_not_called()
    assert result == {"ok": True, "createdCount": 0, "notificationIds": []}


def test_execute_skips_dispatch_when_pipeline_rejects_recipients(uow):
    user_id = str(uuid4())
    uow.notification_preferences.filter_user_ids_accepting_category.return_value = [
        user_id
    ]

    with patch(
        "app.application.use_cases.send_welcome_notification_use_case.AutomatedNotificationDispatchService"
    ) as service_cls:
        service_cls.return_value.dispatch.side_effect = DispatchNotificationsValidationError(
            "no recipients"
        )
        result = SendWelcomeNotificationUseCase(uow).execute(user_id)

    assert result == {"ok": True, "createdCount": 0, "notificationIds": []}
