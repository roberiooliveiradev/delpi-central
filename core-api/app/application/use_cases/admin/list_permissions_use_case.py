# app/application/use_cases/admin/list_permissions_use_case.py

from app.application.use_cases.admin.base_list_paginated_use_case import BaseListPaginatedUseCase
from app.domain.ports.permission_repository_port import PermissionDTO
from app.application.unit_of_work import UnitOfWork


class ListPermissionsUseCase(BaseListPaginatedUseCase[PermissionDTO]):

    def __init__(self, uow: UnitOfWork):
        super().__init__(uow)

    def execute(self, *, q, page, page_size, sort, direction):

        permissions, total = self.uow.permissions.list_paginated(
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )

        return self._build_result(permissions, total, page, page_size)