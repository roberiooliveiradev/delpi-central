# list_roles_use_case.py

from app.application.use_cases.admin.base_list_paginated_use_case import (
    BaseListPaginatedUseCase,
)
from app.domain.ports.role_repository_port import RoleDTO
from app.application.unit_of_work import UnitOfWork


class ListRolesUseCase(BaseListPaginatedUseCase[RoleDTO]):

    def __init__(self, uow: UnitOfWork):
        super().__init__(uow)

    def execute(self, *, page: int, page_size: int, sort: str, direction: str):
        roles, total = self.uow.roles.list_paginated(
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )

        return self._build_result(roles, total, page, page_size)