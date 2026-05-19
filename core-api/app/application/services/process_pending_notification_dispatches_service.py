# app/application/services/process_pending_notification_dispatches_service.py

from app.application.use_cases.manage_notification_templates_use_case import (
    build_template_registry,
)
from app.application.use_cases.process_pending_notification_dispatches_use_case import (
    ProcessPendingDispatchesResult,
    ProcessPendingNotificationDispatchesUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


def run_process_pending_notification_dispatches(*, limit: int = 20) -> ProcessPendingDispatchesResult:
    registry = build_template_registry()
    with SqlAlchemyUnitOfWork() as uow:
        return ProcessPendingNotificationDispatchesUseCase(
            uow,
            template_registry=registry,
        ).execute(limit=limit)
