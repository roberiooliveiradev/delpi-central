from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from app.application.services.financial.financial_sheet_scope import (
    CONSOLIDATED_BRANCH_KEY,
)


class GetFinancialFixedCostPctUseCase:
    def __init__(
        self,
        financial_metrics_snapshot_service: FinancialMetricsSnapshotService,
    ) -> None:
        self._financial_metrics_snapshot_service = financial_metrics_snapshot_service

    def execute(self, request: GetRolRequest) -> dict:
        snapshot = self._financial_metrics_snapshot_service.get_snapshot(
            start_date=request.start_date,
            end_date=request.end_date,
            branch=request.branch,
        )

        if request.branch:
            branch_snapshot = next(
                (item for item in snapshot.branches if item.branch == request.branch),
                None,
            )

            if branch_snapshot is None:
                return {
                    "branch": request.branch,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "fixed_cost_value": 0.0,
                    "rol_with_ipi": 0.0,
                    "fixed_cost_over_rol_pct": 0.0,
                }

            return {
                "branch": branch_snapshot.branch,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "fixed_cost_value": branch_snapshot.fixed_cost_value,
                "rol_with_ipi": branch_snapshot.rol_with_ipi,
                "fixed_cost_over_rol_pct": branch_snapshot.fixed_cost_over_rol_pct,
            }

        branches = [
            {
                "branch": item.branch,
                "fixed_cost_value": item.fixed_cost_value,
                "rol_with_ipi": item.rol_with_ipi,
                "fixed_cost_over_rol_pct": item.fixed_cost_over_rol_pct,
            }
            for item in snapshot.branches
            if item.branch != CONSOLIDATED_BRANCH_KEY
        ]

        consolidated_snapshot = next(
            (item for item in snapshot.branches if item.branch == CONSOLIDATED_BRANCH_KEY),
            None,
        )
        consolidated_value = (
            consolidated_snapshot.fixed_cost_over_rol_pct
            if consolidated_snapshot
            and consolidated_snapshot.fixed_cost_over_rol_pct is not None
            else 0.0
        )

        return {
            "branch": None,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "fixed_cost_over_rol_pct": consolidated_value,
            "branches": branches,
        }