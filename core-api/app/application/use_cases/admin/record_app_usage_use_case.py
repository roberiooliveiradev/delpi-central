# app/application/use_cases/admin/record_app_usage_use_case.py

from datetime import datetime, timedelta
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    SqlAlchemyAppUsageRepository,
)


class RecordAppUsageUseCase:

    DEBOUNCE_MINUTES = 5

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = SqlAlchemyAppUsageRepository(uow.session)

    def execute(
        self,
        *,
        user_id: str,
        session_id: str,
        app_id: str,
        route_path: str | None = None,
    ) -> None:
        normalized_app_id = str(app_id).strip()
        if not normalized_app_id:
            return

        if is_app_usage_enabled():
            store = get_app_usage_live_store()
            store.set_active_app(
                session_id,
                app_id=normalized_app_id,
                route_path=route_path,
            )

        try:
            user_uuid = UUID(str(user_id))
        except ValueError:
            return

        now = datetime.utcnow()
        since = now - timedelta(minutes=self.DEBOUNCE_MINUTES)

        if self.repo.has_recent_open(
            user_id=user_uuid,
            app_id=normalized_app_id,
            since=since,
        ):
            return

        self.repo.record_open(
            user_id=user_uuid,
            app_id=normalized_app_id,
            route_path=route_path,
            opened_at=now,
        )
