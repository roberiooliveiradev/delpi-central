from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class LookupDirectoryUsersUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, *, user_ids: list[str]) -> list[dict]:
        normalized_ids: list[UUID] = []

        for value in user_ids:
            try:
                normalized_ids.append(UUID(str(value).strip()))
            except (TypeError, ValueError):
                continue

        if not normalized_ids:
            return []

        users = self.uow.users.get_by_ids(normalized_ids)

        return [
            {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
            }
            for user in users
            if user.active
        ]
