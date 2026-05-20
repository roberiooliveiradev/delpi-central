# app/application/use_cases/delete_notification_dispatch_use_case.py

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class DeleteNotificationDispatchUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, dispatch_id: UUID, *, actor_user_id: str | None = None) -> dict:
        dispatch = self.uow.notification_dispatches.get(dispatch_id)
        if not dispatch:
            raise DispatchNotificationsValidationError("Dispatch not found")

        notification_ids = self._parse_notification_ids(dispatch.notification_ids)
        deleted_notifications = 0

        if notification_ids:
            deleted_notifications = self.uow.notifications.soft_delete_many(notification_ids)

        if dispatch.status == "pending" and not notification_ids:
            self.uow.notification_dispatches.delete(dispatch_id)
            self._collect_event(
                dispatch_id=dispatch_id,
                actor_user_id=actor_user_id,
                deleted_notifications=0,
                deleted_dispatch=True,
            )
            return {
                "ok": True,
                "deletedDispatch": True,
                "deletedNotifications": 0,
            }

        payload = dict(dispatch.payload or {})
        payload["revokedAt"] = datetime.utcnow().isoformat() + "Z"
        if actor_user_id:
            payload["revokedByUserId"] = actor_user_id

        dispatch.notification_ids = []
        dispatch.created_count = 0
        dispatch.payload = payload
        self.uow.notification_dispatches.update(dispatch)

        self._collect_event(
            dispatch_id=dispatch_id,
            actor_user_id=actor_user_id,
            deleted_notifications=deleted_notifications,
            deleted_dispatch=False,
        )

        return {
            "ok": True,
            "deletedDispatch": False,
            "deletedNotifications": deleted_notifications,
        }

    def _collect_event(
        self,
        *,
        dispatch_id: UUID,
        actor_user_id: str | None,
        deleted_notifications: int,
        deleted_dispatch: bool,
    ) -> None:
        self.uow.collect_event(
            AdminChangedEvent(
                entity="notification_dispatches",
                action="dispatch_revoked",
                payload={
                    "dispatchId": str(dispatch_id),
                    "deletedNotifications": deleted_notifications,
                    "deletedDispatch": deleted_dispatch,
                    "actorUserId": actor_user_id,
                },
            )
        )

    @staticmethod
    def _parse_notification_ids(raw_ids: list[str] | None) -> list[UUID]:
        if not raw_ids:
            return []

        parsed: list[UUID] = []
        for raw in raw_ids:
            try:
                parsed.append(UUID(str(raw)))
            except (TypeError, ValueError):
                continue
        return parsed
