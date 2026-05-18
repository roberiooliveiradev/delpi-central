# app/application/use_cases/process_pending_notification_dispatches_use_case.py

from dataclasses import dataclass

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.process_notification_dispatch_use_case import (
    ProcessNotificationDispatchUseCase,
)
from app.domain.notifications.notification_template_registry import NotificationTemplateRegistry


@dataclass
class ProcessPendingDispatchesResult:
    processed: int
    completed: int
    failed: int
    errors: list[dict]


class ProcessPendingNotificationDispatchesUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        template_registry: NotificationTemplateRegistry | None = None,
    ):
        self.uow = uow
        self.template_registry = template_registry or NotificationTemplateRegistry()

    def execute(self, *, limit: int = 20) -> ProcessPendingDispatchesResult:
        safe_limit = max(1, min(limit, 50))
        pending = self.uow.notification_dispatches.list_due_pending(limit=safe_limit)

        completed = 0
        failed = 0
        errors: list[dict] = []

        processor = ProcessNotificationDispatchUseCase(
            self.uow,
            template_registry=self.template_registry,
        )

        for dispatch in pending:
            if not dispatch.id:
                continue

            try:
                result = processor.execute(dispatch.id)
                if result.status == "completed":
                    completed += 1
                else:
                    failed += 1
                    errors.append(
                        {
                            "dispatchId": str(dispatch.id),
                            "error": result.error_message or "unknown",
                        }
                    )
            except Exception as exc:
                failed += 1
                errors.append({"dispatchId": str(dispatch.id), "error": str(exc)})

        return ProcessPendingDispatchesResult(
            processed=len(pending),
            completed=completed,
            failed=failed,
            errors=errors,
        )
