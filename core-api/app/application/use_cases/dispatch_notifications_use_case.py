from uuid import UUID

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.dto.dispatch_notifications_response import DispatchNotificationsResponse
from app.application.services.notification_recipient_resolution import (
    resolve_notification_recipient_ids,
)
from app.application.services.notification_content_service import (
    NotificationContentService,
    NotificationContentValidationError,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.notifications.notification_recipient_vars import build_recipient_template_vars
from app.domain.notifications.notification_template_registry import NotificationTemplateRegistry
from app.domain.notifications.per_recipient_policy import requires_per_recipient_render
from app.domain.ports.notification_repository import NotificationDTO


class DispatchNotificationsValidationError(ValueError):
    pass


class DispatchNotificationsUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        template_registry: NotificationTemplateRegistry | None = None,
    ):
        self.uow = uow
        self.content_service = NotificationContentService()
        self.template_registry = template_registry or NotificationTemplateRegistry()

    def execute(self, request: DispatchNotificationsRequest) -> DispatchNotificationsResponse:
        target_user_ids = self._resolve_target_user_ids(request)
        if not target_user_ids:
            raise DispatchNotificationsValidationError(
                "at least one recipient is required (broadcast, userIds, emails, roleIds or groupIds)"
            )

        dispatch_category = (request.category or "system").strip().lower()
        target_user_ids = self.uow.notification_preferences.filter_user_ids_accepting_category(
            target_user_ids,
            dispatch_category,
        )
        if not target_user_ids:
            raise DispatchNotificationsValidationError(
                "no recipients accept this notification category (check user preferences)"
            )

        template_spec = self._resolve_template_spec(request)
        per_recipient = requires_per_recipient_render(
            presentation=request.presentation,
            template_spec=template_spec,
            title=request.title,
            message=request.message,
            html_content=request.html_content,
            action_label=request.action_label,
        )

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
                    template_spec=template_spec,
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
                        template_spec=template_spec,
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

    def _resolve_template_spec(self, request: DispatchNotificationsRequest):
        presentation = (request.presentation or "text").strip().lower()
        if presentation != "template" or not request.metadata:
            return None

        template_id = request.metadata.get("templateId") or request.metadata.get("template_id")
        if not template_id or not isinstance(template_id, str):
            return None

        spec = self.template_registry.get(template_id.strip())
        if not spec:
            raise DispatchNotificationsValidationError(f"unknown templateId: {template_id}")
        return spec

    def _resolve_target_user_ids(self, request: DispatchNotificationsRequest) -> list[str]:
        return resolve_notification_recipient_ids(self.uow, request)

    @staticmethod
    def _normalize_user_id(raw_user_id: str) -> str:
        try:
            return str(UUID(str(raw_user_id).strip()))
        except (TypeError, ValueError) as exc:
            raise DispatchNotificationsValidationError(f"invalid user id: {raw_user_id}") from exc
