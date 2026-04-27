# app/application/use_cases/list_group_users_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class ListGroupUsersUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str):
        gid = UUID(group_id)

        group = self.uow.groups.get(gid)
        if not group:
            raise ValueError("Grupo não encontrado.")

        user_ids = self.uow.user_groups.list_user_ids_by_group_id(gid)

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