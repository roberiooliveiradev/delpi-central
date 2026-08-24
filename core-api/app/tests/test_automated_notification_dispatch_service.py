# app/tests/test_automated_notification_dispatch_service.py

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.dto.notification_dispatch_response import NotificationDispatchResponse
from app.application.services.automated_notification_dispatch_service import (
    AutomatedNotificationDispatchService,
)
from app.domain.notifications.notification_automation import SOURCE_APP_RBAC_AUTOMATION


@pytest.fixture
def uow():
    mock = MagicMock()
    mock.notification_dispatches = MagicMock()
    return mock


def _request(**overrides) -> DispatchNotificationsRequest:
    defaults = {
        "title": "Novo acesso liberado",
        "message": "Olá, Maria! Você recebeu acesso a: App.",
        "type": "info",
        "category": "access",
        "presentation": "template",
        "html_content": None,
        "action_type": "portal_route",
        "action_label": "Ver aplicativos",
        "action_target": "/apps",
        "icon": "key-round",
        "metadata": {
            "templateId": "app_access_granted_v1",
            "vars": {"userName": "Maria", "appNames": "App"},
        },
        "expires_at": None,
        "broadcast": False,
        "user_ids": [str(uuid4())],
        "emails": [],
        "role_ids": [],
        "group_ids": [],
        "source_app": SOURCE_APP_RBAC_AUTOMATION,
    }
    defaults.update(overrides)
    return DispatchNotificationsRequest(**defaults)


def test_dispatch_delegates_to_create_notification_dispatch_use_case(uow):
    request = _request()
    dispatch_id = uuid4()
    expected = NotificationDispatchResponse(
        dispatch_id=str(dispatch_id),
        status="completed",
        scheduled_at=None,
        created_count=1,
        notification_ids=[str(uuid4())],
        recipient_count=1,
    )

    with patch(
        "app.application.services.automated_notification_dispatch_service.CreateNotificationDispatchUseCase"
    ) as use_case_cls:
        use_case_cls.return_value.execute.return_value = expected
        result = AutomatedNotificationDispatchService(uow).dispatch(
            request,
            created_by_user_id=None,
        )

    use_case_cls.return_value.execute.assert_called_once_with(
        request,
        created_by_user_id=None,
        scheduled_at=None,
    )
    assert result == expected


def test_record_completed_persists_completed_dispatch_without_resending(uow):
    notification_id = str(uuid4())
    actor_id = str(uuid4())
    request = _request()
    dispatch_id = uuid4()
    uow.notification_dispatches.create.return_value = dispatch_id

    result = AutomatedNotificationDispatchService(uow).record_completed(
        request,
        notification_ids=[notification_id],
        created_by_user_id=actor_id,
    )

    assert result == dispatch_id
    uow.notification_dispatches.create.assert_called_once()
    created = uow.notification_dispatches.create.call_args[0][0]
    assert created.status == "completed"
    assert created.created_by_user_id == actor_id
    assert created.created_count == 1
    assert created.recipient_count == 1
    assert created.notification_ids == [notification_id]
    assert created.template_id == "app_access_granted_v1"
    assert created.category == "access"
    assert created.source_app == SOURCE_APP_RBAC_AUTOMATION
    assert isinstance(created.processed_at, datetime)
    assert created.payload["sourceApp"] == SOURCE_APP_RBAC_AUTOMATION
