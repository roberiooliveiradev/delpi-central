# app/application/use_cases/admin/record_app_usage_use_case.py

from datetime import datetime, timedelta
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.db.models import App
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    BACKEND_ONLY_APP_TYPE,
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
        caller_app_id: str | None = None,
        source: str = "portal",
    ) -> None:
        normalized_app_id = str(app_id).strip()
        if not normalized_app_id:
            return

        app_type = self._get_app_type(normalized_app_id)
        if app_type == BACKEND_ONLY_APP_TYPE and source == "portal":
            return

        if source == "portal" and is_app_usage_enabled():
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
            caller_app_id=self._normalize_caller_app_id(caller_app_id),
            opened_at=now,
        )

    def _normalize_caller_app_id(self, caller_app_id: str | None) -> str | None:
        if not caller_app_id:
            return None
        normalized = str(caller_app_id).strip()
        if not normalized or len(normalized) > 50:
            return None
        row = self.uow.session.query(App.id).filter(App.id == normalized).first()
        return normalized if row else None

    def _get_app_type(self, app_id: str) -> str | None:
        row = self.uow.session.query(App.type).filter(App.id == app_id).first()
        return row.type if row else None
