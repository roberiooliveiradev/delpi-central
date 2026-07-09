from app.application.dto.ppm.ppm_series_request import PpmSeriesRequest
from app.application.dto.ppm.ppm_series_response import (
    PpmSeriesPointDto,
    PpmSeriesResponse,
)
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.services.charts.chart_series_cache_keys import ppm_series_cache_key
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class GetPpmSeriesUseCase:
    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: PpmSeriesRequest) -> PpmSeriesResponse:
        if request.type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")

        cache_key = ppm_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

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
                    product_prefix=request.product_prefix,
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

        response = PpmSeriesResponse(
            type=request.type,
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            points=points,
        )
        set_cached_chart_series(cache_key, response.to_dict())
        return response

    @staticmethod
    def _from_cached_dict(cached: dict) -> PpmSeriesResponse:
        return PpmSeriesResponse(
            type=cached["type"],
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            points=[
                PpmSeriesPointDto(**point)
                for point in cached.get("points") or []
            ],
        )
