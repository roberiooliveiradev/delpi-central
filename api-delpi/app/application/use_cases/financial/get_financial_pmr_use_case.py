from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from app.application.services.financial.financial_sheet_scope import (
    CONSOLIDATED_BRANCH_KEY,
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
                    "pmr_days": None,
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
            if item.branch != CONSOLIDATED_BRANCH_KEY
        ]

        valid_pmr = [
            float(item["pmr_days"])
            for item in branches
            if item["pmr_days"] is not None
        ]
        consolidated_value = (
            round(sum(valid_pmr) / len(valid_pmr), 2) if valid_pmr else None
        )

        return {
            "branch": None,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "pmr_days": consolidated_value,
            "branches": branches,
        }