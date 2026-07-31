"""Use case — resumo de horas improdutivas."""

from __future__ import annotations

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursQueryRequest,
)
from app.application.services.production.unproductive_hours_response_assembler import (
    UnproductiveHoursResponseAssembler,
)
from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)


class GetProductionUnproductiveHoursSummaryUseCase:
    def __init__(self, repository: UnproductiveHoursRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: UnproductiveHoursQueryRequest) -> dict:
        common = request.filter_kwargs()
        return UnproductiveHoursResponseAssembler.to_summary(
            request=request,
            row=self._repository.get_summary(**common),
            top_resource=self._repository.get_top_resource(**common),
            top_operator=self._repository.get_top_operator(**common),
        )
