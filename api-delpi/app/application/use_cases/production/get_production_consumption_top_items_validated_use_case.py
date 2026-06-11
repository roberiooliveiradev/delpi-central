from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.services.production.production_operational_summary_service import (
    build_period_summary,
)
from app.domain.constants.production_operational import (
    DEFAULT_PRODUCTION_OPERATIONAL_LIMIT,
    MAX_PRODUCTION_OPERATIONAL_LIMIT,
)
from app.domain.ports.production.production_consumption_repository_port import (
    ProductionConsumptionRepositoryPort,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


class GetProductionConsumptionTopItemsValidatedUseCase:
    def __init__(self, repository: ProductionConsumptionRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionOperationalRequest) -> dict:
        period_start, period_end = ProtheusDateRangeService.resolve_closed_open_period(
            date_start=request.date_start,
            date_end=request.date_end,
        )
        limit = min(
            request.limit or DEFAULT_PRODUCTION_OPERATIONAL_LIMIT,
            MAX_PRODUCTION_OPERATIONAL_LIMIT,
        )

        items = self._repository.fetch_top_items_validated(
            date_start=period_start,
            date_end_exclusive=period_end,
            branch=request.branch,
            limit=limit,
        )

        return {
            "items": items,
            "summary": build_period_summary(
                items=items,
                branch=request.branch,
                period_start=period_start,
                period_end_exclusive=period_end,
            ),
            "pagination": {"limit": limit, "offset": 0, "returned": len(items)},
        }
