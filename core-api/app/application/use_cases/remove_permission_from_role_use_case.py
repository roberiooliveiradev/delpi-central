# app/application/use_cases/remove_permission_from_role_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class RemovePermissionFromRoleUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str, permission_code: str):

        rid = UUID(role_id)

        # 1️⃣ Regra de negócio
        self.uow.role_permissions.remove_permission_by_code(
            rid,
            permission_code
        )

        # 2️⃣ Evento global de RBAC
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="permission_removed_from_role",
                payload={
                    "roleId": role_id,
                    "permissionCode": permission_code,
                },
                target_user_id=None,
            )
        )

        return {"ok": True}