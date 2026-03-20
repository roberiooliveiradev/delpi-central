# app/application/use_cases/external_nc/list_external_nc_effectiveness_checks_use_case.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nonconformity_effectiveness_repository import (
    ExternalNonconformityEffectivenessRepositoryPort,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)


class ListExternalNcEffectivenessChecksUseCase:
    def __init__(
        self,
        nonconformity_repository: ExternalNonconformityRepositoryPort,
        effectiveness_repository: ExternalNonconformityEffectivenessRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._effectiveness_repository = effectiveness_repository

    def execute(self, nonconformity_id: str):
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        nc = self._nonconformity_repository.get_by_id(nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade externa não encontrada.")

        return self._effectiveness_repository.list_by_nonconformity_id(nc.id)