from __future__ import annotations

from app.application.dto.commercial.sales_conversion_rate_request import (
    SalesConversionRateRequest,
)
from app.application.dto.commercial.sales_conversion_rate_series_request import (
    SalesConversionRateSeriesRequest,
)
from app.application.dto.commercial.sales_conversion_rate_series_response import (
    SalesConversionRateSeriesPointDto,
    SalesConversionRateSeriesResponse,
)
from app.application.services.charts.chart_series_cache_keys import (
    commercial_sales_conversion_rate_series_cache_key,
)
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.commercial.sales_conversion_rate_repository_port import (
    SalesConversionRateRepositoryPort,
)

FILIAL_01 = "01"
FILIAL_02 = "02"


class GetSalesConversionRateSeriesUseCase:
    def __init__(
        self, *, sales_conversion_rate_repository: SalesConversionRateRepositoryPort
    ):
        self._repository = sales_conversion_rate_repository

    def execute(
        self, request: SalesConversionRateSeriesRequest
    ) -> SalesConversionRateSeriesResponse:
        request.validate()

        cache_key = commercial_sales_conversion_rate_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

        buckets_result = build_period_buckets(
            start_date=request.date_start,
            end_date=request.date_end,
            granularity=request.granularity,
        )

        points: list[SalesConversionRateSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            slice_01 = self._fetch_branch_slice(
                branch=FILIAL_01,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
            )
            slice_02 = self._fetch_branch_slice(
                branch=FILIAL_02,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
            )

            points.append(
                SalesConversionRateSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    conversion_filial_01=slice_01["pct"],
                    conversion_filial_02=slice_02["pct"],
                    qtd_proposals_01=slice_01["qtd_proposals"],
                    qtd_proposals_02=slice_02["qtd_proposals"],
                    qtd_won_01=slice_01["qtd_won"],
                    qtd_won_02=slice_02["qtd_won"],
                )
            )

        response = SalesConversionRateSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            points=points,
        )
        set_cached_chart_series(cache_key, response.to_dict())
        return response

    @staticmethod
    def _from_cached_dict(cached: dict) -> SalesConversionRateSeriesResponse:
        return SalesConversionRateSeriesResponse(
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            points=[
                SalesConversionRateSeriesPointDto(**point)
                for point in cached.get("points") or []
            ],
        )

    def _fetch_branch_slice(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        customer_segment: str | None,
        customer_codes: list[str] | None,
    ) -> dict:
        indicator = self._repository.get_sales_conversion_rate(
            SalesConversionRateRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                customer_segment=customer_segment,
                customer_codes=customer_codes,
            )
        )
        parsed = to_optional_float(indicator.sales_conversion_rate_pct)
        return {
            "pct": None if parsed is None else round(parsed, 2),
            "qtd_proposals": int(indicator.qtd_proposals or 0),
            "qtd_won": int(indicator.qtd_won or 0),
        }
