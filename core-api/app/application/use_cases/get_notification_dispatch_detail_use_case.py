# app/application/use_cases/get_notification_dispatch_detail_use_case.py

from __future__ import annotations

from uuid import UUID

from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.services.dispatch_notifications_serialization import (
    payload_dict_to_request,
)
from app.application.services.notification_app_access_service import (
    filter_user_ids_with_app_access,
)
from app.application.services.notification_recipient_resolution import (
    resolve_notification_recipient_users,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


class GetNotificationDispatchDetailUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, dispatch_id: UUID) -> dict:
        dispatch = self.uow.notification_dispatches.get(dispatch_id)
        if not dispatch:
            raise DispatchNotificationsValidationError("Dispatch not found")

        payload = dispatch.payload or {}
        intended_recipients: list[dict] = []
        eligible_recipient_count: int | None = None

        try:
            request = payload_dict_to_request(payload)
            intended_recipients = resolve_notification_recipient_users(self.uow, request)

            action_target = request.action_target if request.action_type == "portal_route" else None
            eligible_ids = filter_user_ids_with_app_access(
                self.uow,
                [item["id"] for item in intended_recipients],
                source_app=request.source_app,
                action_target=action_target,
                metadata=request.metadata,
            )
            eligible_recipient_count = len(eligible_ids)
        except Exception:
            intended_recipients = []

        delivered_recipients = self._build_delivered_recipients(dispatch)

        created_by = None
        if dispatch.created_by_user_id:
            creator = self.uow.users.get_by_id(UUID(dispatch.created_by_user_id))
            if creator:
                created_by = {
                    "id": str(creator.id),
                    "name": creator.name,
                    "email": creator.email,
                }

        return {
            "dispatch": dispatch,
            "intendedRecipients": intended_recipients,
            "eligibleRecipientCount": eligible_recipient_count,
            "deliveredRecipients": delivered_recipients,
            "createdBy": created_by,
            "targeting": self._build_targeting_summary(payload),
        }

    def _build_delivered_recipients(self, dispatch: NotificationDispatchDTO) -> list[dict]:
        raw_ids = dispatch.notification_ids or []
        if not raw_ids:
            return []

        parsed_ids: list[UUID] = []
        for raw in raw_ids:
            try:
                parsed_ids.append(UUID(str(raw)))
            except (TypeError, ValueError):
                continue

        if not parsed_ids:
            return []

        notifications = self.uow.notifications.list_by_ids(parsed_ids)
        user_cache: dict[str, object] = {}
        items: list[dict] = []

        for notification in notifications:
            user_id = notification.user_id
            if user_id not in user_cache:
                user_cache[user_id] = self.uow.users.get_by_id(UUID(user_id))

            user = user_cache[user_id]
            items.append(
                {
                    "notificationId": str(notification.id),
                    "userId": user_id,
                    "name": user.name if user else "—",
                    "email": user.email if user else "—",
                    "read": bool(notification.read),
                    "createdAt": (
                        notification.created_at.isoformat() + "Z"
                        if notification.created_at
                        else None
                    ),
                }
            )

        items.sort(key=lambda row: (row.get("name") or "", row.get("email") or ""))
        return items

    @staticmethod
    def _build_targeting_summary(payload: dict) -> dict:
        action = payload.get("action") if isinstance(payload.get("action"), dict) else None
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

        return {
            "broadcast": bool(payload.get("broadcast")),
            "userIds": [str(item) for item in (payload.get("userIds") or []) if item],
            "emails": [str(item) for item in (payload.get("emails") or []) if item],
            "roleIds": [str(item) for item in (payload.get("roleIds") or []) if item],
            "groupIds": [str(item) for item in (payload.get("groupIds") or []) if item],
            "permissionCodes": [
                str(item) for item in (payload.get("permissionCodes") or []) if item
            ],
            "excludedUserIds": [
                str(item) for item in (payload.get("excludedUserIds") or []) if item
            ],
            "sourceApp": payload.get("sourceApp") or payload.get("source_app"),
            "actionType": payload.get("actionType") or payload.get("action_type"),
            "actionLabel": payload.get("actionLabel") or payload.get("action_label"),
            "actionTarget": payload.get("actionTarget") or payload.get("action_target"),
            "metadata": metadata,
        }
