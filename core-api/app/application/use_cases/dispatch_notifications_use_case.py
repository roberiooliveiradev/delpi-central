from uuid import UUID

from app.application.dto.dispatch_notifications_request import (
    ALLOWED_NOTIFICATION_TYPES,
    DispatchNotificationsRequest,
)
from app.application.dto.dispatch_notifications_response import (
    DispatchNotificationsResponse,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.ports.notification_repository import NotificationDTO


class DispatchNotificationsValidationError(ValueError):
    pass


class DispatchNotificationsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, request: DispatchNotificationsRequest) -> DispatchNotificationsResponse:
        message = (request.message or "").strip()
        if not message:
            raise DispatchNotificationsValidationError("message is required")

        if len(message) > 500:
            raise DispatchNotificationsValidationError("message must be at most 500 characters")

        title = request.title.strip() if request.title else None
        if title and len(title) > 120:
            raise DispatchNotificationsValidationError("title must be at most 120 characters")

        notification_type = (request.type or "info").strip().lower()
        if notification_type not in ALLOWED_NOTIFICATION_TYPES:
            raise DispatchNotificationsValidationError(
                f"type must be one of: {', '.join(sorted(ALLOWED_NOTIFICATION_TYPES))}"
            )

        target_user_ids = self._resolve_target_user_ids(request)
        if not target_user_ids:
            raise DispatchNotificationsValidationError(
                "at least one recipient is required (broadcast, userIds or emails)"
            )

        notification_ids: list[str] = []

        for user_id in target_user_ids:
            notification_id = self.uow.notifications.create(
                NotificationDTO(
                    id=None,
                    user_id=user_id,
                    title=title,
                    message=message,
                    type=notification_type,
                    read=False,
                    created_at=None,
                )
            )

            notification_ids.append(str(notification_id))

            payload = {"notificationId": str(notification_id)}
            if request.source_app:
                payload["sourceApp"] = request.source_app

            self.uow.collect_event(
                AdminChangedEvent(
                    entity="notifications",
                    action="notification_created",
                    payload=payload,
                    target_user_id=user_id,
                )
            )

        return DispatchNotificationsResponse(
            created_count=len(notification_ids),
            notification_ids=notification_ids,
        )

    def _resolve_target_user_ids(self, request: DispatchNotificationsRequest) -> list[str]:
        if request.broadcast:
            return self._list_active_user_ids()

        resolved: set[str] = set()

        for raw_user_id in request.user_ids:
            user_id = self._normalize_user_id(raw_user_id)
            user = self.uow.users.get_by_id(UUID(user_id))
            if not user or not user.active:
                raise DispatchNotificationsValidationError(f"user not found or inactive: {raw_user_id}")
            resolved.add(user_id)

        for email in request.emails:
            normalized_email = (email or "").strip().lower()
            if not normalized_email:
                continue

            user = self.uow.users.get_by_email(normalized_email)
            if not user or not user.active:
                raise DispatchNotificationsValidationError(
                    f"user not found or inactive for email: {normalized_email}"
                )
            resolved.add(str(user.id))

        return sorted(resolved)

    def _list_active_user_ids(self) -> list[str]:
        return sorted(
            str(user.id)
            for user in self.uow.users.list_all()
            if user.active
        )

    @staticmethod
    def _normalize_user_id(raw_user_id: str) -> str:
        try:
            return str(UUID(str(raw_user_id).strip()))
        except (TypeError, ValueError) as exc:
            raise DispatchNotificationsValidationError(f"invalid user id: {raw_user_id}") from exc
