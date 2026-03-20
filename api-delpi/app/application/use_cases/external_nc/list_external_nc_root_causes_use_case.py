# app/application/use_cases/external_nc/list_external_nc_root_causes_use_case.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.external_nc.external_nonconformity_root_cause_repository import (
    ExternalNonconformityRootCauseRepositoryPort,
)


class ListExternalNcRootCausesUseCase:
    def __init__(
        self,
        nonconformity_repository: ExternalNonconformityRepositoryPort,
        root_cause_repository: ExternalNonconformityRootCauseRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._root_cause_repository = root_cause_repository

    def execute(self, nonconformity_id: str):
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        nonconformity = self._nonconformity_repository.get_by_id(
            nonconformity_id.strip()
        )
        if nonconformity is None:
            raise ValueError("Não conformidade externa não encontrada.")

        return self._root_cause_repository.list_by_nonconformity_id(nonconformity.id)