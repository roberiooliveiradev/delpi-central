# app/application/use_cases/create_notification_dispatch_use_case.py

from datetime import datetime, timedelta

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.dto.notification_dispatch_response import NotificationDispatchResponse
from app.application.services.dispatch_notifications_serialization import (
    extract_template_id,
    request_to_payload_dict,
)
from app.application.unit_of_work import UnitOfWork
from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.process_notification_dispatch_use_case import (
    ProcessNotificationDispatchUseCase,
)
from app.domain.notifications.notification_template_registry import NotificationTemplateRegistry
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


class CreateNotificationDispatchUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        template_registry: NotificationTemplateRegistry | None = None,
    ):
        self.uow = uow
        self.template_registry = template_registry or NotificationTemplateRegistry()

    def execute(
        self,
        request: DispatchNotificationsRequest,
        *,
        created_by_user_id: str | None,
        scheduled_at: datetime | None,
    ) -> NotificationDispatchResponse:
        now = datetime.utcnow()

        if scheduled_at and scheduled_at <= now - timedelta(seconds=30):
            raise DispatchNotificationsValidationError(
                "scheduledAt must be in the future"
            )

        is_scheduled = scheduled_at is not None and scheduled_at > now
        payload = request_to_payload_dict(request)

        dispatch = NotificationDispatchDTO(
            id=None,
            created_by_user_id=created_by_user_id,
            status="pending",
            scheduled_at=scheduled_at if is_scheduled else None,
            processed_at=None,
            broadcast=request.broadcast,
            recipient_count=0,
            created_count=0,
            title=request.title,
            category=request.category,
            presentation=request.presentation,
            template_id=extract_template_id(request.metadata),
            source_app=request.source_app,
            payload=payload,
            notification_ids=None,
            error_message=None,
        )

        dispatch_id = self.uow.notification_dispatches.create(dispatch)

        if is_scheduled:
            return NotificationDispatchResponse(
                dispatch_id=str(dispatch_id),
                status="pending",
                scheduled_at=scheduled_at.isoformat() + "Z",
                created_count=0,
                notification_ids=[],
                recipient_count=0,
            )

        processed = ProcessNotificationDispatchUseCase(
            self.uow,
            template_registry=self.template_registry,
        ).execute(dispatch_id)

        return NotificationDispatchResponse(
            dispatch_id=str(dispatch_id),
            status=processed.status,
            scheduled_at=None,
            created_count=processed.created_count,
            notification_ids=processed.notification_ids or [],
            recipient_count=processed.recipient_count,
            error_message=processed.error_message,
        )
