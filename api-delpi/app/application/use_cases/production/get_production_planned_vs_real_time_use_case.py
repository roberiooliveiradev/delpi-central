from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.services.production.production_operational_summary_service import (
    build_reference_date_summary,
)
from app.domain.constants.production_operational import (
    DEFAULT_PRODUCTION_OPERATIONAL_LIMIT,
    MAX_PRODUCTION_OPERATIONAL_LIMIT,
)
from app.domain.ports.production.production_orders_repository_port import (
    ProductionOrdersRepositoryPort,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


class GetProductionPlannedVsRealTimeUseCase:
    def __init__(self, repository: ProductionOrdersRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionOperationalRequest) -> dict:
        reference_date = ProtheusDateRangeService.resolve_reference_date(
            request.reference_date
        )
        limit = min(
            request.limit or DEFAULT_PRODUCTION_OPERATIONAL_LIMIT,
            MAX_PRODUCTION_OPERATIONAL_LIMIT,
        )

        items = self._repository.fetch_planned_vs_real_time(
            reference_date=reference_date,
            branch=request.branch,
            work_center=request.work_center,
            limit=limit,
        )

        return {
            "reference_date": reference_date,
            "items": items,
            "summary": build_reference_date_summary(
                items=items,
                branch=request.branch,
                reference_date=reference_date,
            ),
            "pagination": {"limit": limit, "offset": 0, "returned": len(items)},
        }
