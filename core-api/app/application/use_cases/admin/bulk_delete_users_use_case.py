# app/application/use_cases/admin/bulk_delete_users_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.admin.delete_user_use_case import DeleteUserUseCase


class BulkDeleteUsersUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_ids: list[str],
        *,
        actor_user_id: str | None = None,
    ) -> dict:
        if not isinstance(user_ids, list):
            raise ValueError("Campo 'ids' deve ser uma lista.")

        deleted = 0
        skipped = 0

        delete_user_use_case = DeleteUserUseCase(self.uow)

        for user_id in user_ids:
            result = delete_user_use_case.execute(
                user_id,
                actor_user_id=actor_user_id,
            )

            if result.get("deleted"):
                deleted += 1
            else:
                skipped += 1

        return {
            "ok": True,
            "deleted": deleted,
            "skipped": skipped,
        }