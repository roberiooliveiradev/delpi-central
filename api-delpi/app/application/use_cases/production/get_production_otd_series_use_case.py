from __future__ import annotations

from app.application.dto.production.production_otd_series_request import (
    ProductionOtdSeriesRequest,
)
from app.application.dto.production.production_otd_series_response import (
    ProductionOtdSeriesPointDto,
    ProductionOtdSeriesResponse,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.production.on_time_delivery_repository_port import (
    OnTimeDeliveryRepositoryPort,
)

FILIAL_01 = "01"
FILIAL_02 = "02"


class GetProductionOtdSeriesUseCase:
    def __init__(
        self,
        on_time_delivery_repository: OnTimeDeliveryRepositoryPort,
    ):
        self._otd_repository = on_time_delivery_repository

    def execute(self, request: ProductionOtdSeriesRequest) -> ProductionOtdSeriesResponse:
        request.validate()

        buckets_result = build_period_buckets(
            date_start=request.date_start,
            date_end=request.date_end,
            granularity=request.granularity,
        )

        points: list[ProductionOtdSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            otd_01 = self._fetch_otd_pct(
                branch=FILIAL_01,
                start_date=bucket.date_start,
                end_date=bucket.date_end,
                include=request.branch in (None, FILIAL_01),
            )
            otd_02 = self._fetch_otd_pct(
                branch=FILIAL_02,
                start_date=bucket.date_start,
                end_date=bucket.date_end,
                include=request.branch in (None, FILIAL_02),
            )

            points.append(
                ProductionOtdSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    date_start=bucket.date_start,
                    date_end=bucket.date_end,
                    otd_filial_01=otd_01,
                    otd_filial_02=otd_02,
                )
            )

        return ProductionOtdSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            branch=request.branch,
            points=points,
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

        otd = self._otd_repository.get_on_time_delivery(
            ProductionRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )

        if otd is None:
            return None

        parsed = to_optional_float(otd.on_time_delivery_pct)
        if parsed is None:
            return None

        return round(parsed, 2)
