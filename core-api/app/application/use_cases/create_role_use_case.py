# app/application/use_cases/create_role_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class CreateRoleUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, name: str, description: str | None):

        if self.uow.roles.exists_by_name(name):
            raise ValueError("Role já existe")

        # 1️⃣ Regra de negócio
        role_id = self.uow.roles.create(name, description)

        # 2️⃣ Evento administrativo (broadcast)
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="role_created",
                payload={
                    "roleId": str(role_id),
                    "name": name,
                },
                target_user_id=None,  # broadcast
            )
        )

        return role_id