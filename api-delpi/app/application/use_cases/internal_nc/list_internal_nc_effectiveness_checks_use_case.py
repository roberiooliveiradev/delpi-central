# app/application/use_cases/internal_nc/list_internal_nc_effectiveness_checks_use_case.py
from __future__ import annotations

from app.domain.ports.internal_nc.internal_nonconformity_effectiveness_repository import (
    InternalNonconformityEffectivenessRepositoryPort,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)


class ListInternalNcEffectivenessChecksUseCase:
    def __init__(
        self,
        nonconformity_repository: InternalNonconformityRepositoryPort,
        effectiveness_repository: InternalNonconformityEffectivenessRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._effectiveness_repository = effectiveness_repository

    def execute(self, nonconformity_id: str):
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        nc = self._nonconformity_repository.get_by_id(nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade interna não encontrada.")

        return self._effectiveness_repository.list_by_nonconformity_id(nc.id)