# app/application/use_cases/update_scheduled_notification_dispatch_use_case.py

from datetime import datetime, timedelta
from uuid import UUID

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.services.dispatch_notifications_serialization import (
    extract_template_id,
    request_to_payload_dict,
)
from app.application.unit_of_work import UnitOfWork
from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


class UpdateScheduledNotificationDispatchUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        dispatch_id: UUID,
        request: DispatchNotificationsRequest,
        *,
        scheduled_at: datetime | None,
    ) -> NotificationDispatchDTO:
        dispatch = self.uow.notification_dispatches.get(dispatch_id)
        if not dispatch:
            raise DispatchNotificationsValidationError("Dispatch not found")

        if dispatch.status != "pending":
            raise DispatchNotificationsValidationError(
                "Only pending dispatches can be edited"
            )

        if not dispatch.scheduled_at:
            raise DispatchNotificationsValidationError(
                "Only scheduled dispatches can be edited"
            )

        now = datetime.utcnow()
        if scheduled_at is None:
            raise DispatchNotificationsValidationError("scheduledAt is required")

        if scheduled_at <= now - timedelta(seconds=30):
            raise DispatchNotificationsValidationError(
                "scheduledAt must be in the future"
            )

        payload = request_to_payload_dict(request)
        updated = NotificationDispatchDTO(
            id=dispatch.id,
            created_by_user_id=dispatch.created_by_user_id,
            status="pending",
            scheduled_at=scheduled_at,
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
            created_at=dispatch.created_at,
        )

        self.uow.notification_dispatches.update(updated)
        return updated
