"""Use case — itens de matérias-primas sem giro (paginado)."""

from __future__ import annotations

from app.application.dto.supplies.non_moving_stock_request import (
    NonMovingStockItemsRequest,
)
from app.application.services.paged_list_envelope_service import (
    build_paged_list_envelope,
)
from app.domain.ports.supplies.non_moving_stock_repository_port import (
    NonMovingStockRepositoryPort,
)
from app.domain.services.supplies import non_moving_stock_service as svc


class GetNonMovingStockItemsUseCase:
    def __init__(self, repository: NonMovingStockRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: NonMovingStockItemsRequest) -> dict:
        window = svc.resolve_consumption_window(
            start_date=request.start_date,
            end_date=request.end_date,
        )
        total = self._repository.count_items(
            branches=request.branches,
            warehouses=request.warehouses,
            window_start=window.start,
            window_end=window.end,
            no_consumption_status=window.no_consumption_status,
            product_codes=request.product_codes,
            turnover_status=request.turnover_status,
            blocked=request.blocked,
            search=request.search,
        )
        items = self._repository.fetch_items(
            branches=request.branches,
            warehouses=request.warehouses,
            window_start=window.start,
            window_end=window.end,
            no_consumption_status=window.no_consumption_status,
            product_codes=request.product_codes,
            turnover_status=request.turnover_status,
            blocked=request.blocked,
            search=request.search,
            sort=request.sort,
            offset=request.offset,
            page_size=request.page_size,
        )
        return build_paged_list_envelope(
            page=request.page,
            page_size=request.page_size,
            total=total,
            items=items,
            extra={
                "sort": request.sort,
                "reference": {
                    "consumption_window_start": _iso(window.start),
                    "consumption_window_end": _iso(window.end),
                    "window_kind": window.kind,
                    "valuation_reference": "sb2_current_snapshot",
                },
            },
        )


def _iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
