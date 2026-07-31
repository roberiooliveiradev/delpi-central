"""Use case — ranking de horas improdutivas por dimensão."""

from __future__ import annotations

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursRankingRequest,
)
from app.application.services.production.unproductive_hours_response_assembler import (
    UnproductiveHoursResponseAssembler,
)
from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)


class GetProductionUnproductiveHoursRankingUseCase:
    def __init__(self, repository: UnproductiveHoursRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: UnproductiveHoursRankingRequest) -> dict:
        rows = self._repository.get_ranking(
            **request.filter_kwargs(),
            rank_by=request.rank_by,
            metric=request.metric,
            limit=request.limit,
        )
        return UnproductiveHoursResponseAssembler.to_ranking(
            request=request, rows=rows
        )
