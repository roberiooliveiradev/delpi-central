"""Use cases — ordens de produção."""

from __future__ import annotations

from app.application.dto.production.pcp_orders_request import (
    PcpOrdersFilterRequest,
    PcpOrdersItemsRequest,
    PcpOrdersRankingRequest,
)
from app.application.services.production.pcp_orders_response_assembler import (
    PcpOrdersResponseAssembler,
)
from app.domain.ports.production.pcp_orders_repository_port import PcpOrdersRepositoryPort


class GetProductionPcpOrdersSummaryUseCase:
    def __init__(self, repository: PcpOrdersRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: PcpOrdersFilterRequest) -> dict:
        row = self._repository.get_summary(**request.filter_kwargs())
        return PcpOrdersResponseAssembler.to_summary(row, request)


class GetProductionPcpOrdersItemsUseCase:
    def __init__(self, repository: PcpOrdersRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: PcpOrdersItemsRequest) -> dict:
        filters = request.filter_kwargs()
        total = self._repository.count_items(**filters)
        rows = self._repository.get_items(
            **filters,
            sort=request.sort,
            offset=request.offset,
            page_size=request.page_size,
        )
        return PcpOrdersResponseAssembler.to_items(rows, total=total, request=request)


class GetProductionPcpOrdersRankingUseCase:
    def __init__(self, repository: PcpOrdersRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: PcpOrdersRankingRequest) -> dict:
        rows = self._repository.get_ranking(
            **request.filter_kwargs(),
            rank_by=request.rank_by,
            metric=request.metric,
            limit=request.limit,
        )
        return PcpOrdersResponseAssembler.to_ranking(rows, request)
