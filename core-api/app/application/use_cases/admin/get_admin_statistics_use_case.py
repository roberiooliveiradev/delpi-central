# app/application/use_cases/admin/get_admin_statistics_use_case.py

from datetime import datetime

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.persistence.sqlalchemy.admin_statistics_repository import (
    SqlAlchemyAdminStatisticsRepository,
)
from app.infrastructure.presence.presence_store_provider import (
    get_user_presence_store,
    is_user_presence_enabled,
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
        snapshot["generatedAt"] = datetime.utcnow().isoformat() + "Z"

        return snapshot
