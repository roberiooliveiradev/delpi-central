from app.application.dto.ppm.ppm_series_request import PpmSeriesRequest
from app.application.dto.ppm.ppm_series_response import (
    PpmSeriesPointDto,
    PpmSeriesResponse,
)
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.shared.chart_period_buckets import build_period_buckets
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class GetPpmSeriesUseCase:
    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: PpmSeriesRequest) -> PpmSeriesResponse:
        if request.type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")

        buckets_result = build_period_buckets(
            date_start=request.date_start,
            date_end=request.date_end,
            granularity=request.granularity,
        )

        points: list[PpmSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            summary = self._repository.get_summary(
                PpmSummaryRequest(
                    type=request.type,
                    branch=request.branch,
                    date_start=bucket.date_start,
                    date_end=bucket.date_end,
                )
            )

            points.append(
                PpmSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    date_start=bucket.date_start,
                    date_end=bucket.date_end,
                    ppm=round(float(summary.ppm or 0), 2),
                    total_devolvido_un=round(float(summary.total_devolvido_un or 0), 2),
                    total_produzido_un=round(float(summary.total_produzido_un or 0), 2),
                )
            )

        return PpmSeriesResponse(
            type=request.type,
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            points=points,
        )
