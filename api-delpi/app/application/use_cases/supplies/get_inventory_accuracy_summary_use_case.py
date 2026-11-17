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
        # A contagem de eventos "corretos" continua diagnóstica, mas o KPI
        # passa a ser a média simples dos percentuais QUANTITATIVOS.
        scored = totals.get("scored_count", 0)
        unscorable = totals.get("unscorable_count", 0)
        quantity_accuracy = svc.mean_quantity_accuracy(
            accuracy_sum=totals.get("quantity_accuracy_sum", 0),
            scored_count=scored,
        )

        status, reason = svc.summarize_availability(
            valid_count=valid, evaluable_count=evaluable
        )

        # Se há contagens processadas mas nenhuma com saldo teórico positivo,
        # não mostrar "0%" de acuracidade: sinalizar indisponibilidade.
        if status == "ok" and quantity_accuracy is None:
            status, reason = "unavailable", "no_scorable_theoretical_quantity"

        by_branch = []
        for row in data["by_branch"]:
            branch_scored = row.get("scored_count", 0)
            by_branch.append({
                **row,
                "accuracy_percentage": svc.mean_quantity_accuracy(
                    accuracy_sum=row.get("quantity_accuracy_sum", 0),
                    scored_count=branch_scored,
                ),
                "accuracy_calculation": "arithmetic_mean_quantity_accuracy",
            })

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
                "accuracy_percentage": quantity_accuracy,
                "accuracy_calculation": "arithmetic_mean_quantity_accuracy",
                "scored_count": scored,
                "unscorable_count": unscorable,
                "coverage_percentage": svc.accuracy_percentage(
                    evaluable, valid
                ),
                "shortage_value_total": totals["shortage_value_total"],
                "surplus_value_total": totals["surplus_value_total"],
                "comparison_source": (
                    "protheus_mata270_quantity_difference"
                ),
                "status": status,
                "unavailable_reason": reason,
            },
            "exclusions": {
                "pending_processing": totals[
                    "excluded_pending_processing"
                ],
                "cancelled": cancelled,
                "unscorable_nonpositive_theoretical": unscorable,
            },
            "by_branch": by_branch,
        }


def _iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
