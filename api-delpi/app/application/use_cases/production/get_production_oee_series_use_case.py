from __future__ import annotations

from app.application.dto.production.production_oee_series_request import (
    ProductionOeeSeriesRequest,
)
from app.application.dto.production.production_oee_series_response import (
    ProductionOeeSeriesPointDto,
    ProductionOeeSeriesResponse,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.services.charts.chart_series_cache_keys import (
    production_oee_series_cache_key,
)
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)

FILIAL_01 = "01"
FILIAL_02 = "02"


class GetProductionOeeSeriesUseCase:
    def __init__(
        self,
        overall_equipment_effectiveness_repository: OverallEquipmentEffectivenessRepositoryPort,
    ):
        self._oee_repository = overall_equipment_effectiveness_repository

    def execute(self, request: ProductionOeeSeriesRequest) -> ProductionOeeSeriesResponse:
        request.validate()

        cache_key = production_oee_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

        buckets_result = build_period_buckets(
            date_start=request.date_start,
            date_end=request.date_end,
            granularity=request.granularity,
        )

        points: list[ProductionOeeSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            oee_01 = self._fetch_oee_pct(
                branch=FILIAL_01,
                start_date=bucket.date_start,
                end_date=bucket.date_end,
                include=request.branch in (None, FILIAL_01),
            )
            oee_02 = self._fetch_oee_pct(
                branch=FILIAL_02,
                start_date=bucket.date_start,
                end_date=bucket.date_end,
                include=request.branch in (None, FILIAL_02),
            )

            points.append(
                ProductionOeeSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    date_start=bucket.date_start,
                    date_end=bucket.date_end,
                    oee_filial_01=oee_01,
                    oee_filial_02=oee_02,
                )
            )

        response = ProductionOeeSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            branch=request.branch,
            points=points,
        )
        set_cached_chart_series(cache_key, response.to_dict())
        return response

    @staticmethod
    def _from_cached_dict(cached: dict) -> ProductionOeeSeriesResponse:
        return ProductionOeeSeriesResponse(
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            branch=cached.get("branch"),
            points=[
                ProductionOeeSeriesPointDto(**point)
                for point in cached.get("points") or []
            ],
        )

    def _fetch_oee_pct(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        include: bool,
    ) -> float | None:
        if not include:
            return None

        oee = self._oee_repository.get_overall_equipment_effectiveness(
            ProductionRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )

        if oee is None:
            return None

        parsed = to_optional_float(oee.oee_pct)
        if parsed is None:
            return None

        return round(parsed, 2)

