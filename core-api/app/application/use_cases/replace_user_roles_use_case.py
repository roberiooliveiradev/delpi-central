# app/application/use_cases/replace_user_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.admin_event_publicher import (
    AdminEventPublisher,
    AdminChangedEvent,
)


class ReplaceUserRolesUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: AdminEventPublisher,
    ):
        self.uow = uow
        self.event_publisher = event_publisher

    def execute(self, user_id: str, role_ids: list[str]):

        uid = UUID(user_id)
        rid_list = [UUID(r) for r in role_ids]

        # 1️⃣ Regra de aplicação
        self.uow.user_roles.replace_roles(uid, rid_list)

        # 2️⃣ Commit transacional
        try:
            self.uow.user_roles.replace_roles(uid, rid_list)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise

        # 3️⃣ Invalida cache
        if getattr(self.uow, "cache", None):
            self.uow.cache.invalidate(user_id)

        # 4️⃣ Publica evento reativo
        self.event_publisher.publish(
            AdminChangedEvent(
                entity="rbac",
                action="roles_replaced",
                payload={"userId": user_id},
                target_user_id=user_id,  
            )
        )

        return {"ok": True}