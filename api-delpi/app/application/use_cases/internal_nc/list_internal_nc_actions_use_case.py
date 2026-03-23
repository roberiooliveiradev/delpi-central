from __future__ import annotations

from app.domain.ports.internal_nc.internal_nonconformity_action_repository import (
    InternalNonconformityActionRepositoryPort,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)


class ListInternalNcActionsUseCase:
    def __init__(
        self,
        nonconformity_repository: InternalNonconformityRepositoryPort,
        action_repository: InternalNonconformityActionRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._action_repository = action_repository

    def execute(self, nonconformity_id: str):
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        nc = self._nonconformity_repository.get_by_id(nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade interna não encontrada.")

        return self._action_repository.list_by_nonconformity_id(nc.id)