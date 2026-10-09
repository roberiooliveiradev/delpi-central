"""Use case — resumo de acuracidade do inventário físico."""

from __future__ import annotations

from app.application.dto.supplies.inventory_accuracy_request import (
    InventoryAccuracyQueryRequest,
)
from app.domain.ports.supplies.inventory_accuracy_repository_port import (
    InventoryAccuracyRepositoryPort,
)
from app.domain.services.supplies import inventory_accuracy_service as svc


class GetInventoryAccuracySummaryUseCase:
    def __init__(self, repository: InventoryAccuracyRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: InventoryAccuracyQueryRequest) -> dict:
        last_closing = self._repository.fetch_last_closing_date(
            branches=request.branches
        )
        period = svc.resolve_accuracy_period(
            month=request.month,
            start_date=request.start_date,
            end_date=request.end_date,
            last_closing_date=last_closing,
        )
        data = self._repository.fetch_summary(
            branches=request.branches,
            period_start=period.period_start,
            period_end_exclusive=period.period_end_exclusive,
        )
        totals = data["totals"]
        cancelled = self._repository.count_cancelled_events(
            branches=request.branches,
            period_start=period.period_start,
            period_end_exclusive=period.period_end_exclusive,
        )

        valid = totals["valid_count_total"]
        evaluable = totals["evaluable_count_total"]
        accurate = totals["accurate_count"]

        status, reason = svc.summarize_availability(
            valid_count=valid, evaluable_count=evaluable
        )

        return {
            "reference": {
                "reference_month": period.reference_month,
                "period_start": _iso(period.period_start),
                "period_end_exclusive": _iso(period.period_end_exclusive),
                "period_kind": period.kind,
                "period_closed": period.closed,
                "branches": list(request.branches),
            },
            "summary": {
                "valid_count_total": valid,
                "evaluable_count_total": evaluable,
                "accurate_count": accurate,
                "divergent_count": totals["divergent_count"],
                "accuracy_percentage": svc.accuracy_percentage(
                    accurate, evaluable
                ),
                "coverage_percentage": svc.accuracy_percentage(
                    evaluable, valid
                ),
                "shortage_value_total": totals["shortage_value_total"],
                "surplus_value_total": totals["surplus_value_total"],
                "comparison_source": (
                    "protheus_mata270_adjustment_decision"
                ),
                "status": status,
                "unavailable_reason": reason,
            },
            "exclusions": {
                "pending_processing": totals[
                    "excluded_pending_processing"
                ],
                "cancelled": cancelled,
            },
            "by_branch": data["by_branch"],
        }


def _iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
