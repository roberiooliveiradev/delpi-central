# app/application/use_cases/replace_user_groups_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class ReplaceUserGroupsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, group_ids: list[str]):

        uid = UUID(user_id)
        gids = [UUID(g) for g in group_ids]

        self.uow.user_groups.replace_groups(uid, gids)

        if self.uow.cache:
            self.uow.cache.invalidate(user_id)

        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="groups_replaced",
                payload={"userId": user_id},
                target_user_id=user_id,
            )
        )

        return {"ok": True}