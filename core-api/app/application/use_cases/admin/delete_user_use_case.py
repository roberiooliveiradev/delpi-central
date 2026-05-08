# app/application/use_cases/admin/delete_user_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class DeleteUserUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> dict:
        uid = UUID(user_id)

        if actor_user_id and str(uid) == str(actor_user_id):
            raise ValueError("Você não pode excluir o próprio usuário autenticado.")

        user = self.uow.users.get_by_id(uid)
        if not user:
            return {"ok": True, "deleted": False}

        if user.is_superadmin:
            raise ValueError("Usuário superadmin não pode ser excluído por esta ação.")

        self.uow.user_roles.delete_by_user_id(uid)
        self.uow.user_groups.delete_by_user_id(uid)

        # Importante:
        # favoritos precisam ser apagados antes do usuário,
        # porque user_favorite_apps.user_id é chave obrigatória/PK.
        self.uow.favorites.delete_by_user_id(str(uid))

        self.uow.users.delete(uid)

        return {"ok": True, "deleted": True}