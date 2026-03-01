# app/application/use_cases/add_group_to_user_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class AddGroupToUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, group_id: str):

        uid = UUID(user_id)
        gid = UUID(group_id)

        # 1️⃣ Regra de negócio
        self.uow.user_groups.add_group(uid, gid)

        # 2️⃣ Invalida cache do usuário
        if self.uow.cache:
            self.uow.cache.invalidate(user_id)

        # 3️⃣ Evento direcionado
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="group_added_to_user",
                payload={
                    "userId": user_id,
                    "groupId": group_id,
                },
                target_user_id=user_id,
            )
        )

        return {"ok": True}