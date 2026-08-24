# app/tests/test_process_birthday_notifications_use_case.py

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.dto.notification_dispatch_response import NotificationDispatchResponse
from app.application.use_cases.process_birthday_notifications_use_case import (
    ProcessBirthdayNotificationsUseCase,
)
from app.domain.notifications.notification_automation import SOURCE_APP_BIRTHDAY_AUTOMATION


@pytest.fixture
def uow():
    mock = MagicMock()
    mock.users = MagicMock()
    mock.notifications = MagicMock()
    mock.notification_preferences = MagicMock()
    return mock


def test_execute_sends_single_batch_dispatch_for_eligible_users(uow):
    user_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
    uow.users.list_active_ids_with_birthday_on.return_value = user_ids
    uow.notifications.has_category_notification_on_date.return_value = False
    uow.notification_preferences.filter_user_ids_accepting_category.side_effect = (
        lambda ids, _category: ids
    )

    with patch(
        "app.domain.services.usage_tracking_consent_service.user_has_birthday_notifications_consent",
        return_value=True,
    ), patch(
        "app.application.use_cases.process_birthday_notifications_use_case.AutomatedNotificationDispatchService"
    ) as service_cls:
        service_cls.return_value.dispatch.return_value = NotificationDispatchResponse(
            dispatch_id=str(uuid4()),
            status="completed",
            scheduled_at=None,
            created_count=3,
            notification_ids=[str(uuid4()) for _ in range(3)],
            recipient_count=3,
        )
        result = ProcessBirthdayNotificationsUseCase(uow).execute(on_date=date(2026, 8, 24))

    service_cls.return_value.dispatch.assert_called_once()
    request = service_cls.return_value.dispatch.call_args[0][0]
    assert request.source_app == SOURCE_APP_BIRTHDAY_AUTOMATION
    assert request.user_ids == user_ids
    assert result.eligible == 3
    assert result.sent == 3
    assert result.skipped == 0


def test_execute_skips_dispatch_when_no_eligible_users(uow):
    user_id = str(uuid4())
    uow.users.list_active_ids_with_birthday_on.return_value = [user_id]
    uow.notifications.has_category_notification_on_date.return_value = True

    with patch(
        "app.domain.services.usage_tracking_consent_service.user_has_birthday_notifications_consent",
        return_value=True,
    ), patch(
        "app.application.use_cases.process_birthday_notifications_use_case.AutomatedNotificationDispatchService"
    ) as service_cls:
        result = ProcessBirthdayNotificationsUseCase(uow).execute(on_date=date(2026, 8, 24))

    service_cls.return_value.dispatch.assert_not_called()
    assert result.sent == 0
    assert result.skipped == 1
