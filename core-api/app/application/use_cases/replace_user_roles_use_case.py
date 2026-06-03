# app/application/use_cases/replace_user_roles_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.permission_resolver import PermissionResolver


class ReplaceUserRolesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, role_ids: list[str]):

        uid = UUID(user_id)
        rid_list = [UUID(r) for r in role_ids]
        previous_ids = set(self.uow.user_roles.list_role_ids(uid))
        new_ids = set(rid_list)
        added_role_ids = [str(rid) for rid in rid_list if rid not in previous_ids]
        removed_role_ids = [str(rid) for rid in previous_ids if rid not in new_ids]
        role_set_changed = bool(added_role_ids or removed_role_ids)

        payload: dict = {"userId": user_id}

        if added_role_ids:
            user = self.uow.users.get_by_id(uid)
            if user:
                resolver = PermissionResolver(self.uow.permission_queries, cache=None)
                payload["previousPermissionCodes"] = resolver.resolve(
                    uid,
                    bool(user.is_superadmin),
                )
            payload["addedRoleIds"] = added_role_ids

        if removed_role_ids:
            payload["removedRoleIds"] = removed_role_ids

        # 1️⃣ Regra de negócio
        self.uow.user_roles.replace_roles(uid, rid_list)

        if role_set_changed:
            self.uow.collect_event(
                AdminChangedEvent(
                    entity="rbac",
                    action="roles_replaced",
                    payload=payload,
                    target_user_id=user_id,
                )
            )

        return {"ok": True}