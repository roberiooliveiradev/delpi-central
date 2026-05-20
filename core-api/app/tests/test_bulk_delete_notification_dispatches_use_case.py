# app/tests/test_bulk_delete_notification_dispatches_use_case.py

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.bulk_delete_notification_dispatches_use_case import (
    BulkDeleteNotificationDispatchesUseCase,
)
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


def _dispatch(**kwargs) -> NotificationDispatchDTO:
    defaults = {
        "id": uuid4(),
        "created_by_user_id": str(uuid4()),
        "status": "completed",
        "scheduled_at": None,
        "processed_at": datetime.utcnow(),
        "broadcast": False,
        "recipient_count": 1,
        "created_count": 1,
        "title": "Teste",
        "category": "announcement",
        "presentation": "text",
        "template_id": None,
        "source_app": None,
        "payload": {"message": "Olá"},
        "notification_ids": [str(uuid4())],
        "error_message": None,
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return NotificationDispatchDTO(**defaults)


@pytest.fixture
def uow():
    mock = MagicMock()
    mock.notification_dispatches = MagicMock()
    mock.notifications = MagicMock()
    return mock


def test_bulk_delete_revokes_multiple(uow):
    first = _dispatch()
    second = _dispatch()
    uow.notification_dispatches.get.side_effect = [first, second]
    uow.notifications.soft_delete_many.return_value = 1

    use_case = BulkDeleteNotificationDispatchesUseCase(uow)
    result = use_case.execute([first.id, second.id], actor_user_id="admin-1")

    assert result["revoked"] == 2
    assert result["deletedNotifications"] == 2
    assert result["errors"] == []


def test_bulk_delete_requires_ids(uow):
    use_case = BulkDeleteNotificationDispatchesUseCase(uow)

    with pytest.raises(DispatchNotificationsValidationError, match="dispatchIds is required"):
        use_case.execute([])
