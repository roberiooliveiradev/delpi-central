from uuid import UUID

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.dto.dispatch_notifications_response import DispatchNotificationsResponse
from app.application.services.notification_content_service import (
    NotificationContentService,
    NotificationContentValidationError,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.notifications.notification_recipient_vars import (
    build_recipient_template_vars,
    template_requires_per_recipient_render,
)
from app.domain.notifications.notification_templates import NOTIFICATION_TEMPLATES
from app.domain.ports.notification_repository import NotificationDTO


class DispatchNotificationsValidationError(ValueError):
    pass


class DispatchNotificationsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.content_service = NotificationContentService()

    def execute(self, request: DispatchNotificationsRequest) -> DispatchNotificationsResponse:
        target_user_ids = self._resolve_target_user_ids(request)
        if not target_user_ids:
            raise DispatchNotificationsValidationError(
                "at least one recipient is required (broadcast, userIds or emails)"
            )

        template_spec = self._resolve_template_spec(request)
        per_recipient = template_requires_per_recipient_render(template_spec)

        prepared_shared = None
        if not per_recipient:
            try:
                prepared_shared = self.content_service.prepare(
                    title=request.title,
                    message=request.message,
                    type=request.type,
                    category=request.category,
                    presentation=request.presentation,
                    html_content=request.html_content,
                    action_type=request.action_type,
                    action_label=request.action_label,
                    action_target=request.action_target,
                    icon=request.icon,
                    metadata=request.metadata,
                    expires_at=request.expires_at,
                )
            except NotificationContentValidationError as exc:
                raise DispatchNotificationsValidationError(str(exc)) from exc

        notification_ids: list[str] = []

        for user_id in target_user_ids:
            if per_recipient:
                user = self.uow.users.get_by_id(UUID(user_id))
                if not user:
                    raise DispatchNotificationsValidationError(f"user not found: {user_id}")

                recipient_context = build_recipient_template_vars(user, template_spec)
                try:
                    prepared = self.content_service.prepare(
                        title=request.title,
                        message=request.message,
                        type=request.type,
                        category=request.category,
                        presentation=request.presentation,
                        html_content=request.html_content,
                        action_type=request.action_type,
                        action_label=request.action_label,
                        action_target=request.action_target,
                        icon=request.icon,
                        metadata=request.metadata,
                        expires_at=request.expires_at,
                        recipient_context=recipient_context,
                    )
                except NotificationContentValidationError as exc:
                    raise DispatchNotificationsValidationError(str(exc)) from exc
            else:
                prepared = prepared_shared

            notification_id = self.uow.notifications.create(
                NotificationDTO(
                    user_id=user_id,
                    title=prepared.title,
                    message=prepared.message,
                    type=prepared.type,
                    category=prepared.category,
                    presentation=prepared.presentation,
                    html_content=prepared.html_content,
                    action_type=prepared.action_type,
                    action_label=prepared.action_label,
                    action_target=prepared.action_target,
                    icon=prepared.icon,
                    metadata=prepared.metadata,
                    expires_at=prepared.expires_at,
                    read=False,
                )
            )

            notification_ids.append(str(notification_id))

            event_payload = {
                "notificationId": str(notification_id),
                "category": prepared.category,
            }
            if request.source_app:
                event_payload["sourceApp"] = request.source_app

            self.uow.collect_event(
                AdminChangedEvent(
                    entity="notifications",
                    action="notification_created",
                    payload=event_payload,
                    target_user_id=user_id,
                )
            )

        return DispatchNotificationsResponse(
            created_count=len(notification_ids),
            notification_ids=notification_ids,
        )

    @staticmethod
    def _resolve_template_spec(request: DispatchNotificationsRequest):
        presentation = (request.presentation or "text").strip().lower()
        if presentation != "template" or not request.metadata:
            return None

        template_id = request.metadata.get("templateId") or request.metadata.get("template_id")
        if not template_id or not isinstance(template_id, str):
            return None

        return NOTIFICATION_TEMPLATES.get(template_id.strip())

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
