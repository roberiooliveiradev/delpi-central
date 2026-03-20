# app/application/use_cases/external_nc/get_external_nonconformity_details_use_case.py
from __future__ import annotations

from app.domain.entities.external_nc.external_nonconformity import (
    ExternalNonconformity,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)


class GetExternalNonconformityDetailsUseCase:
    def __init__(
        self,
        repository: ExternalNonconformityRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(self, nonconformity_id: str) -> ExternalNonconformity:
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        entity = self._repository.get_by_id(nonconformity_id.strip())

        if entity is None:
            raise ValueError("Não conformidade externa não encontrada.")

        return entity