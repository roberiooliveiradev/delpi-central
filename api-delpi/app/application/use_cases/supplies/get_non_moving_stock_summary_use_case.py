"""Use case — resumo de matérias-primas sem giro."""

from __future__ import annotations

from app.application.dto.supplies.non_moving_stock_request import (
    NonMovingStockQueryRequest,
)
from app.domain.ports.supplies.non_moving_stock_repository_port import (
    NonMovingStockRepositoryPort,
)
from app.domain.services.supplies import non_moving_stock_service as svc


class GetNonMovingStockSummaryUseCase:
    def __init__(self, repository: NonMovingStockRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: NonMovingStockQueryRequest) -> dict:
        window = svc.resolve_consumption_window(
            start_date=request.start_date,
            end_date=request.end_date,
        )
        data = self._repository.fetch_summary(
            branches=request.branches,
            warehouses=request.warehouses,
            window_start=window.start,
            window_end=window.end,
            no_consumption_status=window.no_consumption_status,
        )
        totals = data["totals"]

        eligible = totals["eligible_stock_value"]
        insufficient = totals["insufficient_history_stock_value"]
        evaluable = eligible - insufficient
        no_consumption = totals["no_consumption_stock_value"]

        status, reason = svc.summarize_availability(
            eligible_stock_value=eligible,
            evaluable_stock_value=evaluable,
        )

        return {
            "reference": {
                "consumption_window_start": _iso(window.start),
                "consumption_window_end": _iso(window.end),
                "window_kind": window.kind,
                "valuation_reference": "sb2_current_snapshot",
                "product_type": "MP",
                "branches": list(request.branches),
                "warehouses": list(request.warehouses),
            },
            "summary": {
                "eligible_stock_value": eligible,
                "evaluable_stock_value": evaluable,
                "no_consumption_stock_value": no_consumption,
                "with_consumption_stock_value": totals[
                    "with_consumption_stock_value"
                ],
                "insufficient_history_stock_value": insufficient,
                "non_moving_percentage": svc.percentage(
                    no_consumption, evaluable
                ),
                "coverage_percentage": svc.percentage(evaluable, eligible),
                "blocked_stock_value": totals["blocked_stock_value"],
                "blocked_no_consumption_stock_value": totals[
                    "blocked_no_consumption_stock_value"
                ],
                "status": status,
                "unavailable_reason": reason,
            },
            "counts": {
                "eligible_products": totals["product_count"],
                "with_consumption": totals["with_consumption_count"],
                "no_consumption": totals["no_consumption_count"],
                "insufficient_history": totals[
                    "insufficient_history_count"
                ],
                "blocked_products": totals["blocked_product_count"],
            },
            "by_status": data["by_status"],
            "by_branch": data["by_branch"],
        }


def _iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
