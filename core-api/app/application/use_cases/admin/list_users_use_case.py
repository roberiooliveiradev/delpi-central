# app/application/use_cases/admin/list_users_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.admin.base_list_paginated_use_case import (
    BaseListPaginatedUseCase,
)
from app.domain.dto.paginated_result import PaginatedResult
from app.domain.ports.user_repository_port import UserDTO
from app.infrastructure.presence.presence_store_provider import get_user_presence_store


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
        is_superadmin: bool | None = None,
        role_id: UUID | None = None,
        group_id: UUID | None = None,
        online: str | None = None,
    ) -> PaginatedResult[UserDTO]:

        online_filter = None
        online_user_ids = None

        if online in ("true", "false"):
            online_filter = online
            summaries = get_user_presence_store().list_online()
            online_user_ids = []

            for summary in summaries:
                try:
                    online_user_ids.append(UUID(str(summary.user_id)))
                except ValueError:
                    continue

        users, total = self.uow.users.list_paginated(
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            is_superadmin=is_superadmin,
            role_id=role_id,
            group_id=group_id,
            online_filter=online_filter,
            online_user_ids=online_user_ids,
        )

        return self._build_result(users, total, page, page_size)
