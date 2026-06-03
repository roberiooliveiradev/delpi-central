# app/application/use_cases/replace_role_permissions_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class ReplaceRolePermissionsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str, permission_ids: list[str]):

        rid = UUID(role_id)
        new_ids = {UUID(pid) for pid in permission_ids if pid}
        previous_ids = set(self.uow.role_permissions.list_permission_ids(rid))
        added_permission_ids = [str(pid) for pid in new_ids if pid not in previous_ids]

        # 1️⃣ Regra de negócio
        self.uow.role_permissions.replace_permissions_by_ids(
            rid,
            permission_ids
        )

        payload: dict = {"roleId": role_id}
        if added_permission_ids:
            payload["addedPermissionIds"] = added_permission_ids

        # 4️⃣ Evento global de RBAC
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="role_permissions_replaced",
                payload=payload,
                target_user_id=None,
            )
        )

        return {"ok": True}