from __future__ import annotations

from app.application.dto.supplies.purchase_order_otd_request import PurchaseOrderOtdRequest
from app.application.dto.supplies.purchase_order_otd_series_request import (
    PurchaseOrderOtdSeriesRequest,
)
from app.application.dto.supplies.purchase_order_otd_series_response import (
    PurchaseOrderOtdSeriesPointDto,
    PurchaseOrderOtdSeriesResponse,
)
from app.application.services.charts.chart_series_cache_keys import (
    supplies_purchase_order_otd_series_cache_key,
)
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.supplies.purchase_order_otd_repository_port import (
    PurchaseOrderOtdRepositoryPort,
)

FILIAL_01 = "01"
FILIAL_02 = "02"


class GetPurchaseOrderOtdSeriesUseCase:
    def __init__(self, *, purchase_order_otd_repository: PurchaseOrderOtdRepositoryPort):
        self._repository = purchase_order_otd_repository

    def execute(
        self, request: PurchaseOrderOtdSeriesRequest
    ) -> PurchaseOrderOtdSeriesResponse:
        request.validate()

        cache_key = supplies_purchase_order_otd_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

        buckets_result = build_period_buckets(
            start_date=request.date_start,
            end_date=request.date_end,
            granularity=request.granularity,
        )

        points: list[PurchaseOrderOtdSeriesPointDto] = []
        for bucket in buckets_result.buckets:
            otd_01 = self._fetch_otd_pct(
                branch=FILIAL_01,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                include=request.branch in (None, FILIAL_01),
            )
            otd_02 = self._fetch_otd_pct(
                branch=FILIAL_02,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                include=request.branch in (None, FILIAL_02),
            )
            points.append(
                PurchaseOrderOtdSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    otd_filial_01=otd_01,
                    otd_filial_02=otd_02,
                )
            )

        response = PurchaseOrderOtdSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            branch=request.branch,
            points=points,
        )
        set_cached_chart_series(cache_key, response.to_dict())
        return response

    @staticmethod
    def _from_cached_dict(cached: dict) -> PurchaseOrderOtdSeriesResponse:
        return PurchaseOrderOtdSeriesResponse(
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            branch=cached.get("branch"),
            points=[
                PurchaseOrderOtdSeriesPointDto(**point)
                for point in cached.get("points") or []
            ],
        )

    def _fetch_otd_pct(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        include: bool,
    ) -> float | None:
        if not include:
            return None

        indicator = self._repository.get_purchase_order_otd(
            PurchaseOrderOtdRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )
        parsed = to_optional_float(indicator.purchase_order_otd_pct)
        if parsed is None:
            return None
        return round(parsed, 2)
