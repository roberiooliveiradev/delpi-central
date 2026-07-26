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
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)
from app.domain.services.production.production_oee_series_aggregation_service import (
    resolve_bucket_oee_pct,
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
            start_date=request.date_start,
            end_date=request.date_end,
            granularity=request.granularity,
        )

        daily_rows = self._oee_repository.list_oee_kpi_by_day_and_branch(
            ProductionRequest(
                branch=request.branch,
                start_date=request.date_start,
                end_date=request.date_end,
            )
        )

        points: list[ProductionOeeSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            include_01 = request.branch in (None, FILIAL_01)
            include_02 = request.branch in (None, FILIAL_02)

            oee_01 = (
                resolve_bucket_oee_pct(
                    daily_rows,
                    branch=FILIAL_01,
                    date_start=bucket.start_date,
                    date_end=bucket.end_date,
                )
                if include_01
                else None
            )
            oee_02 = (
                resolve_bucket_oee_pct(
                    daily_rows,
                    branch=FILIAL_02,
                    date_start=bucket.start_date,
                    date_end=bucket.end_date,
                )
                if include_02
                else None
            )

            points.append(
                ProductionOeeSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
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
