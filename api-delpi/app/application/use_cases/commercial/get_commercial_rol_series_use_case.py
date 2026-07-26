from app.application.dto.commercial.commercial_rol_series_request import (
    CommercialRolSeriesRequest,
)
from app.application.dto.commercial.commercial_rol_series_response import (
    CommercialRolSeriesPointDto,
    CommercialRolSeriesResponse,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.services.charts.chart_series_cache_keys import (
    commercial_rol_series_cache_key,
)
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
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

        cache_key = commercial_rol_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

        buckets_result = build_period_buckets(
            start_date=request.date_start,
            end_date=request.date_end,
            granularity=request.granularity,
        )

        points: list[CommercialRolSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            matrix_rol = self._financial_query_repository.get_rol(
                GetRolRequest(
                    branch=HEAD_OFFICE_BRANCH,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    customer_segment=request.customer_segment,
                )
            )
            branch_rol = self._financial_query_repository.get_rol(
                GetRolRequest(
                    branch=BRANCH_OFFICE_BRANCH,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    customer_segment=request.customer_segment,
                )
            )

            points.append(
                CommercialRolSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    rol_matrix=round(float(matrix_rol.get("rol_with_ipi") or 0), 2),
                    rol_branch=round(float(branch_rol.get("rol_with_ipi") or 0), 2),
                )
            )

        response = CommercialRolSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            points=points,
        )
        set_cached_chart_series(cache_key, response.to_dict())
        return response

    @staticmethod
    def _from_cached_dict(cached: dict) -> CommercialRolSeriesResponse:
        return CommercialRolSeriesResponse(
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            points=[
                CommercialRolSeriesPointDto(**point)
                for point in cached.get("points") or []
            ],
        )
