# app/application/use_cases/admin/update_group_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class UpdateGroupUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        group_id: str,
        name: str,
        description: str | None = None,
    ) -> dict:
        gid = UUID(group_id)
        normalized_name = (name or "").strip()

        if not normalized_name:
            raise ValueError("Campo 'name' é obrigatório.")

        group = self.uow.groups.get(gid)
        if not group:
            raise ValueError("Grupo não encontrado.")

        self.uow.groups.update(
            group_id=gid,
            name=normalized_name,
            description=description,
        )

        return {"ok": True}