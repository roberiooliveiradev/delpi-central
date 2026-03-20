from __future__ import annotations

from app.application.dto.internal_nc.list_internal_nonconformities_request import (
    ListInternalNonconformitiesRequest,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)


class ListInternalNonconformitiesUseCase:
    def __init__(self, repository: InternalNonconformityRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: ListInternalNonconformitiesRequest) -> dict:
        return self._repository.list(
            page=max(1, request.page),
            page_size=max(1, min(request.page_size, 100)),
            current_status=self._normalize(request.current_status),
            sector=self._normalize(request.sector),
            search=self._normalize(request.search),
        )

    def _normalize(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None