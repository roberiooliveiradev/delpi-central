# app/tests/test_list_notifications_use_case.py

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.list_notifications_use_case import ListNotificationsUseCase
from app.domain.ports.notification_repository import NotificationDTO


def _dto(*, read: bool, message: str) -> NotificationDTO:
    return NotificationDTO(
        id=uuid4(),
        user_id="user-1",
        title=None,
        message=message,
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
        read=read,
        created_at=datetime.utcnow(),
    )


def test_list_notifications_use_case_returns_pagination():
    uow = MagicMock()
    uow.notifications.list_for_user.return_value = ([_dto(read=False, message="a")], 1)

    result = ListNotificationsUseCase(uow).execute("user-1", status="unread", limit=10, offset=0)

    assert result.total == 1
    assert result.limit == 10
    assert len(result.items) == 1
    uow.notifications.list_for_user.assert_called_once_with(
        "user-1",
        status="unread",
        category=None,
        important_only=False,
        limit=10,
        offset=0,
    )


def test_list_notifications_use_case_passes_category_and_important_filters():
    uow = MagicMock()
    uow.notifications.list_for_user.return_value = ([], 0)

    ListNotificationsUseCase(uow).execute(
        "user-1",
        category="announcement",
        important_only=True,
        limit=20,
        offset=0,
    )

    uow.notifications.list_for_user.assert_called_once_with(
        "user-1",
        status="all",
        category="announcement",
        important_only=True,
        limit=20,
        offset=0,
    )


def test_list_notifications_use_case_clamps_limit():
    uow = MagicMock()
    uow.notifications.list_for_user.return_value = ([], 0)

    result = ListNotificationsUseCase(uow).execute("user-1", limit=500, offset=-5)

    assert result.limit == 100
    assert result.offset == 0
