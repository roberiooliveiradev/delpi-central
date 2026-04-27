# app/application/use_cases/list_role_users_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class ListRoleUsersUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str):
        rid = UUID(role_id)

        role = self.uow.roles.get(rid)
        if not role:
            raise ValueError("Papel não encontrado.")

        user_ids = self.uow.user_roles.list_user_ids_by_role_id(rid)

        users = []

        for uid in user_ids:
            user = self.uow.users.get_by_id(uid)

            if not user:
                continue

            users.append({
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "active": user.active,
                "is_superadmin": user.is_superadmin,
                "last_login_at": (
                    user.last_login_at.isoformat()
                    if user.last_login_at
                    else None
                ),
            })

        return users