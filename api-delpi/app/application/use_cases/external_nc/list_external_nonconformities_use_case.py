# app/application/use_cases/external_nc/list_external_nonconformities_use_case.py
from __future__ import annotations

from app.application.dto.external_nc.list_external_nonconformities_request import (
    ListExternalNonconformitiesRequest,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)


class ListExternalNonconformitiesUseCase:
    def __init__(
        self,
        repository: ExternalNonconformityRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(self, request: ListExternalNonconformitiesRequest) -> dict:
        page = max(1, request.page)
        page_size = max(1, min(request.page_size, 100))

        return self._repository.list(
            page=page,
            page_size=page_size,
            current_status=self._normalize_optional_str(request.current_status),
            supplier_id=self._normalize_optional_str(request.supplier_id),
            search=self._normalize_optional_str(request.search),
        )

    def _normalize_optional_str(self, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None