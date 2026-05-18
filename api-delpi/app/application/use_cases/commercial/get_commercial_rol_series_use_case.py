from app.application.dto.commercial.commercial_rol_series_request import (
    CommercialRolSeriesRequest,
)
from app.application.dto.commercial.commercial_rol_series_response import (
    CommercialRolSeriesPointDto,
    CommercialRolSeriesResponse,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.shared.chart_period_buckets import build_period_buckets
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)

HEAD_OFFICE_BRANCH = "01"
BRANCH_OFFICE_BRANCH = "02"


class GetCommercialRolSeriesUseCase:
    def __init__(self, financial_query_repository: FinancialQueryRepositoryPort):
        self._financial_query_repository = financial_query_repository

    def execute(self, request: CommercialRolSeriesRequest) -> CommercialRolSeriesResponse:
        request.validate()

        buckets_result = build_period_buckets(
            date_start=request.date_start,
            date_end=request.date_end,
            granularity=request.granularity,
        )

        points: list[CommercialRolSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            matrix_rol = self._financial_query_repository.get_rol(
                GetRolRequest(
                    branch=HEAD_OFFICE_BRANCH,
                    start_date=bucket.date_start,
                    end_date=bucket.date_end,
                )
            )
            branch_rol = self._financial_query_repository.get_rol(
                GetRolRequest(
                    branch=BRANCH_OFFICE_BRANCH,
                    start_date=bucket.date_start,
                    end_date=bucket.date_end,
                )
            )

            points.append(
                CommercialRolSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    date_start=bucket.date_start,
                    date_end=bucket.date_end,
                    rol_matrix=round(float(matrix_rol.get("rol_with_ipi") or 0), 2),
                    rol_branch=round(float(branch_rol.get("rol_with_ipi") or 0), 2),
                )
            )

        return CommercialRolSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            points=points,
        )
