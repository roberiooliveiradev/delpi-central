# app/application/use_cases/replace_role_permissions_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class ReplaceRolePermissionsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str, permission_ids: list[str]):

        rid = UUID(role_id)

        # 1️⃣ Regra de negócio
        self.uow.role_permissions.replace_permissions_by_ids(
            rid,
            permission_ids
        )

        # 2️⃣ Descobre usuários impactados
        user_ids = set(self.uow.rbac_queries.list_user_ids_by_role(rid))
        user_ids |= set(self.uow.rbac_queries.list_user_ids_by_group_role(rid))

        # 4️⃣ Evento global de RBAC
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="role_permissions_replaced",
                payload={"roleId": role_id},
                target_user_id=None,
            )
        )

        return {"ok": True}