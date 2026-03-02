# app/application/use_cases/add_group_to_user_use_case.py
from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.iam_sync_service import IamSyncService


class AddGroupToUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, group_id: str):

        uid = UUID(user_id)
        gid = UUID(group_id)

        # Regra de negócio
        self.uow.user_groups.add_group(uid, gid)

        # Evento direcionado
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

