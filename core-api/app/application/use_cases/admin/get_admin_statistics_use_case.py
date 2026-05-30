# app/application/use_cases/admin/get_admin_statistics_use_case.py

from datetime import datetime

from flask import current_app

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.persistence.sqlalchemy.admin_statistics_repository import (
    SqlAlchemyAdminStatisticsRepository,
)
from app.infrastructure.presence.presence_store_provider import (
    get_user_presence_store,
    is_user_presence_enabled,
)
from app.application.use_cases.admin.get_app_usage_snapshot_use_case import (
    GetAppUsageSnapshotUseCase,
)
from app.application.use_cases.admin.get_least_engaged_users_use_case import (
    GetLeastEngagedUsersUseCase,
)


class GetAdminStatisticsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self) -> dict:
        repo = SqlAlchemyAdminStatisticsRepository(self.uow.session)
        snapshot = repo.get_snapshot()

        online_total = 0
        if is_user_presence_enabled():
            online_total = len(get_user_presence_store().list_online())

        snapshot["users"]["online"] = online_total
        history_days = int(current_app.config.get("APP_USAGE_HISTORY_DAYS", 30))
        snapshot["apps"]["usage"] = GetAppUsageSnapshotUseCase(self.uow).execute(
            history_days=history_days,
        )
        snapshot["users"]["leastEngaged"] = GetLeastEngagedUsersUseCase(
            self.uow
        ).execute(history_days=history_days)
        snapshot["generatedAt"] = datetime.utcnow().isoformat() + "Z"

        return snapshot
