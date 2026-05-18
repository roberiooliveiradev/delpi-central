# app/tests/test_delete_notification_use_case.py

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.delete_notification_use_case import DeleteNotificationUseCase
from app.application.use_cases.notification_user_access import NotificationAccessDeniedError
from app.domain.ports.notification_repository import NotificationDTO


def _notification(*, user_id: str) -> NotificationDTO:
    return NotificationDTO(
        id=uuid4(),
        user_id=user_id,
        title=None,
        message="test",
        type="info",
        category="system",
        presentation="text",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata=None,
        expires_at=None,
        read=False,
    )


def test_delete_notification_soft_deletes_owned_notification():
    notification = _notification(user_id="user-1")
    uow = MagicMock()
    uow.notifications.get.return_value = notification

    result = DeleteNotificationUseCase(uow).execute(notification.id, "user-1")

    assert result == {"ok": True}
    uow.notifications.soft_delete.assert_called_once_with(notification.id)


def test_delete_notification_rejects_other_user():
    notification = _notification(user_id="user-2")
    uow = MagicMock()
    uow.notifications.get.return_value = notification

    try:
        DeleteNotificationUseCase(uow).execute(notification.id, "user-1")
        raised = False
    except NotificationAccessDeniedError:
        raised = True

    assert raised
    uow.notifications.soft_delete.assert_not_called()
