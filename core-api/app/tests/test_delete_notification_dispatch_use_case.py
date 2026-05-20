# app/tests/test_delete_notification_dispatch_use_case.py

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.delete_notification_dispatch_use_case import (
    DeleteNotificationDispatchUseCase,
)
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


@pytest.fixture
def uow():
    mock = MagicMock()
    mock.notification_dispatches = MagicMock()
    mock.notifications = MagicMock()
    return mock


def _dispatch(**kwargs) -> NotificationDispatchDTO:
    defaults = {
        "id": uuid4(),
        "created_by_user_id": str(uuid4()),
        "status": "completed",
        "scheduled_at": None,
        "processed_at": datetime.utcnow(),
        "broadcast": False,
        "recipient_count": 2,
        "created_count": 2,
        "title": "Teste",
        "category": "announcement",
        "presentation": "text",
        "template_id": None,
        "source_app": None,
        "payload": {"message": "Olá"},
        "notification_ids": [str(uuid4()), str(uuid4())],
        "error_message": None,
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return NotificationDispatchDTO(**defaults)


def test_delete_revokes_notifications_for_completed_dispatch(uow):
    dispatch = _dispatch()
    uow.notification_dispatches.get.return_value = dispatch
    uow.notifications.soft_delete_many.return_value = 2

    use_case = DeleteNotificationDispatchUseCase(uow)
    result = use_case.execute(dispatch.id, actor_user_id="admin-1")

    assert result["ok"] is True
    assert result["deletedNotifications"] == 2
    assert result["deletedDispatch"] is False
    assert dispatch.created_count == 0
    assert dispatch.notification_ids == []
    assert dispatch.payload["revokedAt"]
    assert dispatch.payload["revokedByUserId"] == "admin-1"
    uow.notification_dispatches.update.assert_called_once_with(dispatch)


def test_delete_pending_dispatch_without_notifications(uow):
    dispatch_id = uuid4()
    dispatch = _dispatch(
        id=dispatch_id,
        status="pending",
        scheduled_at=datetime.utcnow(),
        notification_ids=None,
        created_count=0,
    )
    uow.notification_dispatches.get.return_value = dispatch

    use_case = DeleteNotificationDispatchUseCase(uow)
    result = use_case.execute(dispatch_id)

    assert result["deletedDispatch"] is True
    assert result["deletedNotifications"] == 0
    uow.notification_dispatches.delete.assert_called_once_with(dispatch_id)
    uow.notification_dispatches.update.assert_not_called()


def test_delete_dispatch_not_found(uow):
    uow.notification_dispatches.get.return_value = None

    use_case = DeleteNotificationDispatchUseCase(uow)

    with pytest.raises(DispatchNotificationsValidationError, match="Dispatch not found"):
        use_case.execute(uuid4())
