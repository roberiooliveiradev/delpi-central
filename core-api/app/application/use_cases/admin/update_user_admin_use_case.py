# app/application/use_cases/admin/update_user_admin_use_case.py

from datetime import date
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.set_user_superadmin_use_case import SetUserSuperadminUseCase
from app.application.use_cases.replace_user_roles_use_case import ReplaceUserRolesUseCase
from app.application.use_cases.replace_user_groups_use_case import ReplaceUserGroupsUseCase


class UpdateUserAdminUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        actor_id: str,
        actor_is_superadmin: bool,
        target_user_id: str,
        role_ids: list[str] | None = None,
        group_ids: list[str] | None = None,
        is_superadmin: bool | None = None,
        birth_date: date | None = None,
        clear_birth_date: bool = False,
    ) -> dict:
        if clear_birth_date:
            self.uow.users.set_birth_date(UUID(target_user_id), None)
        elif birth_date is not None:
            self.uow.users.set_birth_date(UUID(target_user_id), birth_date)
        if is_superadmin is not None:
            set_superadmin_use_case = SetUserSuperadminUseCase(self.uow)

            result = set_superadmin_use_case.execute(
                actor_id=actor_id,
                target_user_id=target_user_id,
                is_superadmin=bool(is_superadmin),
                actor_is_superadmin=actor_is_superadmin,
            )

            if isinstance(result, tuple):
                return result

        if role_ids is not None:
            replace_roles_use_case = ReplaceUserRolesUseCase(self.uow)
            replace_roles_use_case.execute(target_user_id, role_ids)

        if group_ids is not None:
            replace_groups_use_case = ReplaceUserGroupsUseCase(self.uow)
            replace_groups_use_case.execute(target_user_id, group_ids)

        return {"ok": True}