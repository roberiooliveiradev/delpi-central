# app/application/use_cases/list_admin_apps_use_case.py

from datetime import datetime

from app.application.unit_of_work import UnitOfWork


class ListAdminAppsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        page: int,
        page_size: int,
        q: str | None,
        sort: str,
        direction: str,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
    ):
        return self.uow.admin_apps.list_paginated(
            page=page,
            page_size=page_size,
            q=q,
            sort=sort,
            direction=direction,
            created_from=created_from,
            created_to=created_to,
            updated_from=updated_from,
            updated_to=updated_to,
        )