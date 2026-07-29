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
from app.application.use_cases.ppm.get_ppm_summary_use_case import GetPpmSummaryUseCase


class GetPpmSeriesUseCase:
    def __init__(self, summary_use_case: GetPpmSummaryUseCase):
        self._summary_use_case = summary_use_case

    def execute(self, request: PpmSeriesRequest) -> PpmSeriesResponse:
        if request.type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")

        cache_key = ppm_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

        buckets_result = build_period_buckets(
            start_date=request.date_start,
            end_date=request.date_end,
            granularity=request.granularity,
        )

        points: list[PpmSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            summary = self._summary_use_case.execute(
                PpmSummaryRequest(
                    type=request.type,
                    branch=request.branch,
                    date_start=bucket.start_date,
                    date_end=bucket.end_date,
                    product_prefix=request.product_prefix,
                )
            )

            devolvido = round(float(summary.total_devolvido_un or 0), 2)
            produzido_un = round(float(summary.total_produzido_un or 0), 2)
            produzido_milheiro = round(float(summary.total_produzido_milheiro or 0), 4)
            points.append(
                PpmSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    ppm=round(float(summary.ppm or 0), 2),
                    total_devolvido_un=devolvido,
                    total_produzido_un=produzido_un,
                    total_produzido_milheiro=produzido_milheiro,
                    numerator={"qty_returned_un": devolvido},
                    denominator={
                        "qty_produced_un": produzido_un,
                        "qty_produced_milheiro": produzido_milheiro,
                    },
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
        points: list[PpmSeriesPointDto] = []
        for point in cached.get("points") or []:
            devolvido = float(point.get("total_devolvido_un") or 0)
            produzido_un = float(point.get("total_produzido_un") or 0)
            produzido_milheiro = float(point.get("total_produzido_milheiro") or 0)
            points.append(
                PpmSeriesPointDto(
                    periodo=point["periodo"],
                    sort_key=point["sort_key"],
                    start_date=point["start_date"],
                    end_date=point["end_date"],
                    ppm=float(point.get("ppm") or 0),
                    total_devolvido_un=devolvido,
                    total_produzido_un=produzido_un,
                    total_produzido_milheiro=produzido_milheiro,
                    numerator=point.get("numerator")
                    or {"qty_returned_un": devolvido},
                    denominator=point.get("denominator")
                    or {
                        "qty_produced_un": produzido_un,
                        "qty_produced_milheiro": produzido_milheiro,
                    },
                )
            )
        return PpmSeriesResponse(
            type=cached["type"],
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            points=points,
        )
