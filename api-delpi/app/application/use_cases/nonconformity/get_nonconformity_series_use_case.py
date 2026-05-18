from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.application.dto.nonconformity.nonconformity_series_request import (
    NonconformitySeriesRequest,
)
from app.application.dto.nonconformity.nonconformity_series_response import (
    NonconformitySeriesPointDto,
    NonconformitySeriesResponse,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.domain.ports.nonconformity.nonconformity_query_repository_port import (
    NonconformityQueryRepositoryPort,
)


class GetNonconformitySeriesUseCase:
    def __init__(self, repository: NonconformityQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: NonconformitySeriesRequest) -> NonconformitySeriesResponse:
        if request.type not in {"internal", "external", "all"}:
            raise ValueError("type deve ser internal, external ou all")

        buckets_result = build_period_buckets(
            date_start=request.date_start,
            date_end=request.date_end,
            granularity=request.granularity,
        )

        list_request = ListNonconformityRequest(
            type=request.type,
            branch=request.branch,
            status=request.status,
            item_code=request.item_code,
            description=request.description,
        )

        points: list[NonconformitySeriesPointDto] = []

        for bucket in buckets_result.buckets:
            total, registros = self._repository.sum_returned_quantity(
                list_request,
                regist_date_start=bucket.date_start,
                regist_date_end=bucket.date_end,
            )

            points.append(
                NonconformitySeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    date_start=bucket.date_start,
                    date_end=bucket.date_end,
                    value=round(total, 2),
                    registros=registros,
                )
            )

        return NonconformitySeriesResponse(
            type=request.type,
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            points=points,
        )
