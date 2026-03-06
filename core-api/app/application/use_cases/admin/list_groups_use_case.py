# app/application/use_cases/admin/list_groups_use_case.py

from app.application.use_cases.admin.base_list_paginated_use_case import BaseListPaginatedUseCase
from app.domain.ports.group_repository_port import GroupDTO
from app.application.unit_of_work import UnitOfWork


class ListGroupsUseCase(BaseListPaginatedUseCase[GroupDTO]):

    def __init__(self, uow: UnitOfWork):
        super().__init__(uow)

    def execute(self, *, q, page, page_size, sort, direction):

        groups, total = self.uow.groups.list_paginated(
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )

        return self._build_result(groups, total, page, page_size)