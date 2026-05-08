# app/application/use_cases/admin/create_group_use_case.py

from app.application.unit_of_work import UnitOfWork


class CreateGroupUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> dict:
        normalized_name = (name or "").strip()

        if not normalized_name:
            raise ValueError("Campo 'name' é obrigatório.")

        group_id = self.uow.groups.create(
            name=normalized_name,
            description=description,
        )

        return {"id": str(group_id)}