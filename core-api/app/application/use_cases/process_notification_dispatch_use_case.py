# app/application/use_cases/process_notification_dispatch_use_case.py

from datetime import datetime
from uuid import UUID

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.services.dispatch_notifications_serialization import payload_dict_to_request
from app.application.unit_of_work import UnitOfWork
from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsUseCase,
)
from app.domain.notifications.notification_template_registry import NotificationTemplateRegistry
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


class ProcessNotificationDispatchUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        template_registry: NotificationTemplateRegistry | None = None,
    ):
        self.uow = uow
        self.template_registry = template_registry or NotificationTemplateRegistry()

    def execute(self, dispatch_id: UUID) -> NotificationDispatchDTO:
        dispatch = self.uow.notification_dispatches.get(dispatch_id)
        if not dispatch:
            raise DispatchNotificationsValidationError(f"dispatch not found: {dispatch_id}")

        if dispatch.status == "completed":
            return dispatch

        if dispatch.status == "processing":
            raise DispatchNotificationsValidationError(
                f"dispatch already processing: {dispatch_id}"
            )

        dispatch.status = "processing"
        self.uow.notification_dispatches.update(dispatch)

        try:
            request = payload_dict_to_request(dispatch.payload)
            result = DispatchNotificationsUseCase(
                self.uow,
                template_registry=self.template_registry,
            ).execute(request)

            dispatch.status = "completed"
            dispatch.processed_at = datetime.utcnow()
            dispatch.created_count = result.created_count
            dispatch.recipient_count = result.created_count
            dispatch.notification_ids = result.notification_ids
            dispatch.error_message = None
        except Exception as exc:
            dispatch.status = "failed"
            dispatch.processed_at = datetime.utcnow()
            dispatch.error_message = str(exc)
            self.uow.notification_dispatches.update(dispatch)
            raise

        self.uow.notification_dispatches.update(dispatch)
        return dispatch
