"""Use case — série diária de horas improdutivas."""

from __future__ import annotations

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursSeriesRequest,
)
from app.application.services.production.unproductive_hours_response_assembler import (
    UnproductiveHoursResponseAssembler,
)
from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)


class GetProductionUnproductiveHoursSeriesUseCase:
    def __init__(self, repository: UnproductiveHoursRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: UnproductiveHoursSeriesRequest) -> dict:
        return UnproductiveHoursResponseAssembler.to_series(
            request=request,
            rows=self._repository.get_series(**request.filter_kwargs()),
        )
