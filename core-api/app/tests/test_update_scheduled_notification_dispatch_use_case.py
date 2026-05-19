# app/tests/test_update_scheduled_notification_dispatch_use_case.py

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.update_scheduled_notification_dispatch_use_case import (
    UpdateScheduledNotificationDispatchUseCase,
)
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


class FakeNotificationDispatchRepository:
    def __init__(self, dispatch: NotificationDispatchDTO | None):
        self.dispatch = dispatch
        self.updated: NotificationDispatchDTO | None = None

    def get(self, dispatch_id):
        if self.dispatch and self.dispatch.id == dispatch_id:
            return self.dispatch
        return None

    def update(self, dispatch: NotificationDispatchDTO) -> None:
        self.updated = dispatch
        self.dispatch = dispatch


class FakeUnitOfWork:
    def __init__(self, dispatch: NotificationDispatchDTO | None):
        self.notification_dispatches = FakeNotificationDispatchRepository(dispatch)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _scheduled_dispatch() -> NotificationDispatchDTO:
    return NotificationDispatchDTO(
        id=uuid4(),
        created_by_user_id="actor-1",
        status="pending",
        scheduled_at=datetime.utcnow() + timedelta(hours=2),
        processed_at=None,
        broadcast=False,
        recipient_count=0,
        created_count=0,
        title="Old title",
        category="announcement",
        presentation="text",
        template_id=None,
        source_app="portal-admin",
        payload={"message": "old", "userIds": []},
        notification_ids=None,
        error_message=None,
        created_at=datetime.utcnow(),
    )


def test_update_scheduled_dispatch_changes_payload_and_schedule():
    dispatch = _scheduled_dispatch()
    uow = FakeUnitOfWork(dispatch)
    new_time = datetime.utcnow() + timedelta(days=1)

    request = DispatchNotificationsRequest(
        title="New title",
        message="New message",
        type="info",
        category="announcement",
        presentation="text",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata=None,
        expires_at=None,
        broadcast=False,
        user_ids=["550e8400-e29b-41d4-a716-446655440000"],
        emails=[],
        role_ids=[],
        group_ids=[],
        source_app="portal-admin",
    )

    result = UpdateScheduledNotificationDispatchUseCase(uow).execute(
        dispatch.id,
        request,
        scheduled_at=new_time,
    )

    assert result.title == "New title"
    assert result.scheduled_at == new_time
    assert uow.notification_dispatches.updated is not None
    assert uow.notification_dispatches.updated.payload["message"] == "New message"


def test_update_rejects_completed_dispatch():
    dispatch = _scheduled_dispatch()
    dispatch.status = "completed"
    uow = FakeUnitOfWork(dispatch)

    request = DispatchNotificationsRequest(
        title="X",
        message="Y",
        type="info",
        category="announcement",
        presentation="text",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata=None,
        expires_at=None,
        broadcast=False,
        user_ids=[],
        emails=[],
        role_ids=[],
        group_ids=[],
        source_app=None,
    )

    with pytest.raises(DispatchNotificationsValidationError, match="pending"):
        UpdateScheduledNotificationDispatchUseCase(uow).execute(
            dispatch.id,
            request,
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
        )
