# app/application/use_cases/bulk_delete_notification_dispatches_use_case.py

from __future__ import annotations

from uuid import UUID

from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.delete_notification_dispatch_use_case import (
    DeleteNotificationDispatchUseCase,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent

MAX_BULK_DELETE = 50


class BulkDeleteNotificationDispatchesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        dispatch_ids: list[UUID],
        *,
        actor_user_id: str | None = None,
    ) -> dict:
        if not dispatch_ids:
            raise DispatchNotificationsValidationError("dispatchIds is required")

        if len(dispatch_ids) > MAX_BULK_DELETE:
            raise DispatchNotificationsValidationError(
                f"Maximum {MAX_BULK_DELETE} dispatches per request"
            )

        unique_ids = list(dict.fromkeys(dispatch_ids))
        deleter = DeleteNotificationDispatchUseCase(self.uow)

        revoked = 0
        deleted_notifications = 0
        deleted_dispatches = 0
        errors: list[dict] = []

        for dispatch_id in unique_ids:
            try:
                result = deleter.execute(dispatch_id, actor_user_id=actor_user_id)
                revoked += 1
                deleted_notifications += int(result.get("deletedNotifications") or 0)
                if result.get("deletedDispatch"):
                    deleted_dispatches += 1
            except DispatchNotificationsValidationError as exc:
                errors.append({"dispatchId": str(dispatch_id), "error": str(exc)})

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notification_dispatches",
                action="dispatch_bulk_revoked",
                payload={
                    "requested": len(unique_ids),
                    "revoked": revoked,
                    "deletedNotifications": deleted_notifications,
                    "deletedDispatches": deleted_dispatches,
                    "errors": errors,
                    "actorUserId": actor_user_id,
                },
            )
        )

        return {
            "ok": len(errors) == 0,
            "requested": len(unique_ids),
            "revoked": revoked,
            "deletedNotifications": deleted_notifications,
            "deletedDispatches": deleted_dispatches,
            "errors": errors,
        }
