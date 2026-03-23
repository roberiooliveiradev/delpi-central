from __future__ import annotations

from app.domain.ports.internal_nc.internal_nc_details_repository import (
    InternalNcDetailsRepositoryPort,
)


class GetInternalNonconformityFullDetailsUseCase:
    def __init__(
        self,
        details_repository: InternalNcDetailsRepositoryPort,
    ) -> None:
        self._details_repository = details_repository

    def execute(self, nonconformity_id: str) -> dict:
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        payload = self._details_repository.get_full_details(nonconformity_id.strip())
        if payload is None:
            raise ValueError("Não conformidade interna não encontrada.")

        return payload