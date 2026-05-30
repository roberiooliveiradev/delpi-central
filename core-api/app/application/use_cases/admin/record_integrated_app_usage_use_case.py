# app/application/use_cases/admin/record_integrated_app_usage_use_case.py

from enum import Enum
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.admin.record_app_usage_use_case import (
    RecordAppUsageUseCase,
)
from app.domain.services.usage_tracking_consent_service import (
    user_has_usage_tracking_consent,
)
from app.infrastructure.db.models import App


class RecordIntegratedAppUsageResult(str, Enum):
    RECORDED = "recorded"
    SKIPPED_CONSENT = "skipped_consent"
    INVALID = "invalid"


class RecordIntegratedAppUsageUseCase:
    """Registra uso de apps backend-only (ou outros) via service token."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        app_id: str,
        user_id: str,
        route_path: str | None = None,
        caller_app_id: str | None = None,
    ) -> RecordIntegratedAppUsageResult:
        normalized_app_id = str(app_id).strip()
        if not normalized_app_id:
            return RecordIntegratedAppUsageResult.INVALID

        try:
            user_uuid = UUID(str(user_id))
        except ValueError:
            return RecordIntegratedAppUsageResult.INVALID

        app = (
            self.uow.session.query(App.id)
            .filter(App.id == normalized_app_id, App.active.is_(True))
            .first()
        )
        if not app:
            return RecordIntegratedAppUsageResult.INVALID

        if not user_has_usage_tracking_consent(self.uow, user_uuid):
            return RecordIntegratedAppUsageResult.SKIPPED_CONSENT

        RecordAppUsageUseCase(self.uow).execute(
            user_id=str(user_uuid),
            session_id=f"integration:{normalized_app_id}:{user_uuid}",
            app_id=normalized_app_id,
            route_path=route_path,
            caller_app_id=caller_app_id,
            source="integration",
        )
        return RecordIntegratedAppUsageResult.RECORDED
