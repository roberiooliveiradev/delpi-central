from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)


class GetFinancialPmrUseCase:
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
                    "pmr_days": 0.0,
                }

            return {
                "branch": branch_snapshot.branch,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "pmr_days": branch_snapshot.pmr_days,
            }

        branches = [
            {
                "branch": item.branch,
                "pmr_days": item.pmr_days,
            }
            for item in snapshot.branches
        ]

        consolidated_value = (
            round(sum(item["pmr_days"] for item in branches) / len(branches), 2)
            if branches
            else 0.0
        )

        return {
            "branch": None,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "pmr_days": consolidated_value,
            "branches": branches,
        }