"""Use case — itens paginados de horas improdutivas."""

from __future__ import annotations

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursItemsRequest,
)
from app.application.services.production.unproductive_hours_response_assembler import (
    UnproductiveHoursResponseAssembler,
)
from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)


class GetProductionUnproductiveHoursItemsUseCase:
    def __init__(self, repository: UnproductiveHoursRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: UnproductiveHoursItemsRequest) -> dict:
        common = request.filter_kwargs()
        total = self._repository.count_items(**common)
        rows = self._repository.get_items(
            **common,
            sort=request.sort,
            offset=request.offset,
            page_size=request.page_size,
        )
        return UnproductiveHoursResponseAssembler.to_items(
            request=request, total=total, rows=rows
        )
