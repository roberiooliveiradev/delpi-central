# app/application/use_cases/list_admin_apps_use_case.py

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
    ):
        return self.uow.admin_apps.list_paginated(
            page=page,
            page_size=page_size,
            q=q,
            sort=sort,
            direction=direction,
        )