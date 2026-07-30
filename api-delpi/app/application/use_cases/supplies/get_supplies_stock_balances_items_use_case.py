"""Use case — itens de saldo por armazém (paginado)."""

from __future__ import annotations

from app.application.dto.supplies.stock_balances_request import StockBalancesItemsRequest
from app.domain.ports.supplies.stock_balances_query_repository_port import (
    StockBalancesQueryRepositoryPort,
)


class GetSuppliesStockBalancesItemsUseCase:
    def __init__(self, repository: StockBalancesQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: StockBalancesItemsRequest) -> dict:
        total = self._repository.count_items(
            branch=request.branch,
            warehouse=request.warehouse,
            only_positive=request.only_positive,
        )
        items = self._repository.fetch_items(
            branch=request.branch,
            warehouse=request.warehouse,
            only_positive=request.only_positive,
            sort=request.sort,
            offset=request.offset,
            page_size=request.page_size,
        )
        total_pages = (
            (total + request.page_size - 1) // request.page_size if total else 0
        )
        return {
            "items": items,
            "page": request.page,
            "page_size": request.page_size,
            "total": total,
            "total_pages": total_pages,
            "sort": request.sort,
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total": total,
                "total_pages": total_pages,
                "is_complete": request.page >= total_pages if total_pages else True,
            },
        }
