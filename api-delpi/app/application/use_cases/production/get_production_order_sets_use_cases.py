"""Use cases — conjuntos de ordens de produção incompletos."""

from __future__ import annotations

from app.application.dto.production.production_order_sets_request import (
    IncompleteOrderSetsRequest,
)
from app.application.services.production.production_order_sets_response_assembler import (
    ProductionOrderSetsResponseAssembler,
)
from app.domain.ports.production.production_order_sets_repository_port import (
    ProductionOrderSetsRepositoryPort,
)


class GetProductionOrderSetsIncompleteUseCase:
    def __init__(self, repository: ProductionOrderSetsRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: IncompleteOrderSetsRequest) -> dict:
        filters = request.filter_kwargs()
        summary_row = self._repository.get_incomplete_sets_summary(**filters)
        rows = self._repository.get_incomplete_sets(
            **filters,
            offset=request.offset,
            page_size=request.page_size,
        )
        return ProductionOrderSetsResponseAssembler.to_incomplete_sets(
            rows, summary_row=summary_row, request=request
        )
