"""Use case — resumo de saldos por armazém."""

from __future__ import annotations

from app.application.dto.supplies.stock_balances_request import StockBalancesQueryRequest
from app.domain.ports.supplies.stock_balances_query_repository_port import (
    StockBalancesQueryRepositoryPort,
)


class GetSuppliesStockBalancesSummaryUseCase:
    def __init__(self, repository: StockBalancesQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: StockBalancesQueryRequest) -> dict:
        return self._repository.fetch_summary(
            branch=request.branch,
            warehouse=request.warehouse,
            only_positive=request.only_positive,
        )
