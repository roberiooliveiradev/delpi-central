# app/application/use_cases/replace_user_groups_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.permission_resolver import PermissionResolver


class ReplaceUserGroupsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, group_ids: list[str]):

        uid = UUID(user_id)
        gids = [UUID(g) for g in group_ids]
        previous_ids = set(self.uow.user_groups.list_group_ids(uid))
        new_ids = set(gids)
        added_group_ids = [str(gid) for gid in gids if gid not in previous_ids]
        removed_group_ids = [str(gid) for gid in previous_ids if gid not in new_ids]
        group_set_changed = bool(added_group_ids or removed_group_ids)

        payload: dict = {"userId": user_id}

        if added_group_ids:
            user = self.uow.users.get_by_id(uid)
            if user:
                resolver = PermissionResolver(self.uow.permission_queries, cache=None)
                payload["previousPermissionCodes"] = resolver.resolve(
                    uid,
                    bool(user.is_superadmin),
                )
            payload["addedGroupIds"] = added_group_ids

        if removed_group_ids:
            payload["removedGroupIds"] = removed_group_ids

        self.uow.user_groups.replace_groups(uid, gids)

        if group_set_changed:
            self.uow.collect_event(
                AdminChangedEvent(
                    entity="rbac",
                    action="groups_replaced",
                    payload=payload,
                    target_user_id=user_id,
                )
            )

        return {"ok": True}