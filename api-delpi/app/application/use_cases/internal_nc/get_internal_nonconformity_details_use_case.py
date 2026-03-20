from __future__ import annotations

from app.domain.entities.internal_nc.internal_nonconformity import (
    InternalNonconformity,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)


class GetInternalNonconformityDetailsUseCase:
    def __init__(self, repository: InternalNonconformityRepositoryPort) -> None:
        self._repository = repository

    def execute(self, nonconformity_id: str) -> InternalNonconformity:
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        entity = self._repository.get_by_id(nonconformity_id.strip())
        if entity is None:
            raise ValueError("Não conformidade interna não encontrada.")
        return entity