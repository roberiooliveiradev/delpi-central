from __future__ import annotations

from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.dto.commercial.sales_order_otd_series_request import (
    SalesOrderOtdSeriesRequest,
)
from app.application.dto.commercial.sales_order_otd_series_response import (
    SalesOrderOtdSeriesPointDto,
    SalesOrderOtdSeriesResponse,
)
from app.application.services.charts.chart_series_cache_keys import (
    commercial_sales_order_otd_series_cache_key,
)
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.commercial.sales_order_otd_repository_port import (
    SalesOrderOtdRepositoryPort,
)

FILIAL_01 = "01"
FILIAL_02 = "02"


class GetSalesOrderOtdSeriesUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepositoryPort):
        self._repository = sales_order_otd_repository

    def execute(self, request: SalesOrderOtdSeriesRequest) -> SalesOrderOtdSeriesResponse:
        request.validate()

        cache_key = commercial_sales_order_otd_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

        buckets_result = build_period_buckets(
            date_start=request.date_start,
            date_end=request.date_end,
            granularity=request.granularity,
        )

        points: list[SalesOrderOtdSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            otd_01 = self._fetch_otd_pct(
                branch=FILIAL_01,
                start_date=bucket.date_start,
                end_date=bucket.date_end,
                customer_segment=request.customer_segment,
                include=request.branch in (None, FILIAL_01),
            )
            otd_02 = self._fetch_otd_pct(
                branch=FILIAL_02,
                start_date=bucket.date_start,
                end_date=bucket.date_end,
                customer_segment=request.customer_segment,
                include=request.branch in (None, FILIAL_02),
            )

            points.append(
                SalesOrderOtdSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    date_start=bucket.date_start,
                    date_end=bucket.date_end,
                    otd_filial_01=otd_01,
                    otd_filial_02=otd_02,
                )
            )

        response = SalesOrderOtdSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            branch=request.branch,
            points=points,
        )
        set_cached_chart_series(cache_key, response.to_dict())
        return response

    @staticmethod
    def _from_cached_dict(cached: dict) -> SalesOrderOtdSeriesResponse:
        return SalesOrderOtdSeriesResponse(
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            branch=cached.get("branch"),
            points=[
                SalesOrderOtdSeriesPointDto(**point)
                for point in cached.get("points") or []
            ],
        )

    def _fetch_otd_pct(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        customer_segment: str | None,
        include: bool,
    ) -> float | None:
        if not include:
            return None

        indicator = self._repository.get_sales_order_otd(
            SalesOrderOtdRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                customer_segment=customer_segment,
            )
        )

        parsed = to_optional_float(indicator.sales_order_otd_pct)
        if parsed is None:
            return None

        return round(parsed, 2)
