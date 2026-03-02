# app/application/use_cases/add_permission_to_role_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.iam_sync_service import IamSyncService

class AddPermissionToRoleUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str, permission_code: str):

        rid = UUID(role_id)

        # Regra de negócio
        self.uow.role_permissions.add_permission_by_code(
            rid,
            permission_code
        )

        # Usuários impactados
        user_ids = set(self.uow.rbac_queries.list_user_ids_by_role(rid))
        user_ids |= set(self.uow.rbac_queries.list_user_ids_by_group_role(rid))

        # Evento global
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="permission_added_to_role",
                payload={
                    "roleId": role_id,
                    "permissionCode": permission_code,
                },
                target_user_id=None,
            )
        )

        return {"ok": True}