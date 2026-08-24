# app/application/services/automated_notification_dispatch_service.py

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.dto.notification_dispatch_response import NotificationDispatchResponse
from app.application.services.dispatch_notifications_serialization import (
    extract_template_id,
    request_to_payload_dict,
)
from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.create_notification_dispatch_use_case import (
    CreateNotificationDispatchUseCase,
)
from app.domain.notifications.notification_template_registry import NotificationTemplateRegistry
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


class AutomatedNotificationDispatchService:

    def __init__(
        self,
        uow: UnitOfWork,
        template_registry: NotificationTemplateRegistry | None = None,
    ):
        self.uow = uow
        self.template_registry = template_registry or NotificationTemplateRegistry()

    def dispatch(
        self,
        request: DispatchNotificationsRequest,
        *,
        created_by_user_id: str | None = None,
    ) -> NotificationDispatchResponse:
        return CreateNotificationDispatchUseCase(
            self.uow,
            template_registry=self.template_registry,
        ).execute(
            request,
            created_by_user_id=created_by_user_id,
            scheduled_at=None,
        )

    def record_completed(
        self,
        request: DispatchNotificationsRequest,
        *,
        notification_ids: list[str],
        created_by_user_id: str | None = None,
    ) -> UUID:
        normalized_ids = [str(item).strip() for item in notification_ids if str(item).strip()]
        created_count = len(normalized_ids)
        now = datetime.utcnow()
        payload = request_to_payload_dict(request)

        dispatch = NotificationDispatchDTO(
            id=None,
            created_by_user_id=created_by_user_id,
            status="completed",
            scheduled_at=None,
            processed_at=now,
            broadcast=request.broadcast,
            recipient_count=created_count,
            created_count=created_count,
            title=request.title,
            category=request.category,
            presentation=request.presentation,
            template_id=extract_template_id(request.metadata),
            source_app=request.source_app,
            payload=payload,
            notification_ids=normalized_ids or None,
            error_message=None,
        )

        return self.uow.notification_dispatches.create(dispatch)
