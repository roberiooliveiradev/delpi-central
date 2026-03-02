# app/application/use_cases/update_role_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class UpdateRoleUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        role_id: str,
        name: str,
        description: str | None,
    ):

        rid = UUID(role_id)

        # 1️⃣ Verifica existência
        role = self.uow.roles.get(rid)
        if not role:
            raise ValueError("Role não encontrada")

        # 2️⃣ Regra de negócio — evitar nome duplicado
        if role.name != name and self.uow.roles.exists_by_name(name):
            raise ValueError("Já existe uma role com esse nome")

        # 3️⃣ Persistência
        self.uow.roles.update(
            role_id=rid,
            name=name,
            description=description,
        )

        # 4️⃣ Evento administrativo (broadcast)
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="role_updated",
                payload={
                    "roleId": str(rid),
                    "name": name,
                },
                target_user_id=None,  # broadcast
            )
        )

        return {"ok": True}