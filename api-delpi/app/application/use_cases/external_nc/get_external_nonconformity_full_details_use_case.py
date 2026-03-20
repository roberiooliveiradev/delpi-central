# app/application/use_cases/external_nc/get_external_nonconformity_full_details_use_case.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nc_details_repository import (
    ExternalNcDetailsRepositoryPort,
)


class GetExternalNonconformityFullDetailsUseCase:
    def __init__(
        self,
        details_repository: ExternalNcDetailsRepositoryPort,
    ) -> None:
        self._details_repository = details_repository

    def execute(self, nonconformity_id: str) -> dict:
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        payload = self._details_repository.get_full_details(nonconformity_id.strip())
        if payload is None:
            raise ValueError("Não conformidade externa não encontrada.")

        return payload