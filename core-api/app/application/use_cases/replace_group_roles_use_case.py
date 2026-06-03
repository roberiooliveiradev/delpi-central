# app/application/use_cases/replace_group_roles_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class ReplaceGroupRolesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str, role_ids: list[str]):

        gid = UUID(group_id)
        rid_list = [UUID(r) for r in role_ids]
        previous_ids = set(self.uow.group_roles.list_role_ids(gid))
        new_ids = set(rid_list)
        added_role_ids = [str(rid) for rid in rid_list if rid not in previous_ids]
        removed_role_ids = [str(rid) for rid in previous_ids if rid not in new_ids]
        role_set_changed = bool(added_role_ids or removed_role_ids)

        payload: dict = {"groupId": group_id}
        if added_role_ids:
            payload["addedRoleIds"] = added_role_ids
        if removed_role_ids:
            payload["removedRoleIds"] = removed_role_ids

        # 1️⃣ Regra de negócio
        self.uow.group_roles.replace_roles(gid, rid_list)

        if not role_set_changed:
            return {"ok": True}

        # Um evento por membro → socket na room do usuário (tempo real no portal)
        member_ids = self.uow.rbac_queries.list_user_ids_by_group(gid)
        for member_id in member_ids:
            self.uow.collect_event(
                AdminChangedEvent(
                    entity="rbac",
                    action="group_roles_replaced",
                    payload=payload,
                    target_user_id=str(member_id),
                )
            )

        return {"ok": True}