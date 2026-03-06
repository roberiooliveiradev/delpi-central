# app/application/use_cases/admin/list_users_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.admin.base_list_paginated_use_case import (
    BaseListPaginatedUseCase,
)
from app.domain.dto.paginated_result import PaginatedResult
from app.domain.ports.user_repository_port import UserDTO


class ListUsersUseCase(BaseListPaginatedUseCase[UserDTO]):

    def __init__(self, uow: UnitOfWork):
        super().__init__(uow)

    def execute(
        self,
        *,
        q: str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> PaginatedResult[UserDTO]:

        users, total = self.uow.users.list_paginated(
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )

        return self._build_result(users, total, page, page_size)