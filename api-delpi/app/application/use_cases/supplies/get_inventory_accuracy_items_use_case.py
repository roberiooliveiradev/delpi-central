"""Use case — eventos de acuracidade do inventário (paginado)."""

from __future__ import annotations

from app.application.dto.supplies.inventory_accuracy_request import (
    InventoryAccuracyItemsRequest,
)
from app.application.services.paged_list_envelope_service import (
    build_paged_list_envelope,
)
from app.domain.ports.supplies.inventory_accuracy_repository_port import (
    InventoryAccuracyRepositoryPort,
)
from app.domain.services.supplies import inventory_accuracy_service as svc


class GetInventoryAccuracyItemsUseCase:
    def __init__(self, repository: InventoryAccuracyRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: InventoryAccuracyItemsRequest) -> dict:
        last_closing = self._repository.fetch_last_closing_date(
            branches=request.branches
        )
        period = svc.resolve_accuracy_period(
            month=request.month,
            start_date=request.start_date,
            end_date=request.end_date,
            last_closing_date=last_closing,
        )
        total = self._repository.count_items(
            branches=request.branches,
            period_start=period.period_start,
            period_end_exclusive=period.period_end_exclusive,
            outcome=request.outcome,
        )
        items = self._repository.fetch_items(
            branches=request.branches,
            period_start=period.period_start,
            period_end_exclusive=period.period_end_exclusive,
            outcome=request.outcome,
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
                    "reference_month": period.reference_month,
                    "period_start": _iso(period.period_start),
                    "period_end_exclusive": _iso(period.period_end_exclusive),
                    "period_kind": period.kind,
                    "period_closed": period.closed,
                },
            },
        )


def _iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
