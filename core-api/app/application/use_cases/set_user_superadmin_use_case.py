# app/application/use_cases/set_user_superadmin_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.interfaces.http.utils.errors import forbidden, bad_request


class SetUserSuperadminUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        actor_id: str,
        target_user_id: str,
        is_superadmin: bool,
        actor_is_superadmin: bool,
    ):

        if not actor_is_superadmin:
            return forbidden("Apenas superadmin pode alterar outro superadmin")

        target_uuid = UUID(target_user_id)

        # 🔎 Buscar estado atual
        target_user = self.uow.users.get_by_id(target_uuid)
        if not target_user:
            return bad_request("Usuário não encontrado")

        current_is_superadmin = bool(target_user.is_superadmin)

        # 🔥 Só validar se estamos realmente removendo um superadmin
        if current_is_superadmin and not is_superadmin:

            total_superadmins = self.uow.users.count_superadmins()

            # Se ele é o último
            if total_superadmins <= 1:
                return bad_request(
                    "O sistema deve possuir pelo menos 1 superadmin"
                )

        # 🔄 Se não houve mudança, não faz nada
        if current_is_superadmin == is_superadmin:
            return {"ok": True}

        # Atualiza flag
        self.uow.users.set_superadmin(target_uuid, is_superadmin)

        # Evento
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="user_superadmin_updated",
                payload={
                    "userId": target_user_id,
                    "is_superadmin": is_superadmin,
                },
                target_user_id=target_user_id,  # agora direcionado
            )
        )

        return {"ok": True}