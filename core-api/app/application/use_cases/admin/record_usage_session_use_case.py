# app/application/use_cases/admin/record_usage_session_use_case.py

from datetime import datetime
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.services.usage_tracking_consent_service import (
    user_has_usage_tracking_consent,
)
from app.domain.usage.usage_session_constants import (
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
)
from app.infrastructure.persistence.sqlalchemy.usage_session_repository import (
    SqlAlchemyUsageSessionRepository,
)


class RecordUsageSessionUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = SqlAlchemyUsageSessionRepository(uow.session)

    def execute(
        self,
        *,
        user_id: str,
        app_id: str | None,
        route_path: str | None,
        started_at: datetime,
        ended_at: datetime,
        source: str,
        socket_session_id: str | None = None,
        max_duration_seconds: int = DEFAULT_MAX_SESSION_DURATION_SECONDS,
    ) -> bool:
        try:
            user_uuid = UUID(str(user_id))
        except ValueError:
            return False

        if not user_has_usage_tracking_consent(self.uow, user_uuid):
            return False

        if ended_at <= started_at:
            return False

        duration_seconds = int((ended_at - started_at).total_seconds())
        duration_seconds = max(1, min(duration_seconds, max_duration_seconds))

        normalized_app_id = str(app_id).strip() if app_id else None
        if normalized_app_id == "":
            normalized_app_id = None

        self.repo.record_session(
            user_id=user_uuid,
            app_id=normalized_app_id,
            route_path=route_path,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            source=source,
            socket_session_id=socket_session_id,
        )
        return True
