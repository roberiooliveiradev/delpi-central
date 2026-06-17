from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.services.production.operational_limit_page_service import (
    build_operational_pagination,
    overfetch_limit,
    trim_overfetched,
)
from app.application.services.production.production_operational_summary_service import (
    build_reference_date_summary,
)
from app.domain.constants.production_operational import (
    DEFAULT_PRODUCTION_OPERATIONAL_LIMIT,
    MAX_PRODUCTION_OPERATIONAL_LIMIT,
)
from app.domain.ports.production.production_work_centers_repository_port import (
    ProductionWorkCentersRepositoryPort,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


class GetProductionWorkCenterOrderSummaryUseCase:
    def __init__(self, repository: ProductionWorkCentersRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionOperationalRequest) -> dict:
        reference_date = ProtheusDateRangeService.resolve_reference_date(
            request.reference_date
        )
        limit = min(
            request.limit or DEFAULT_PRODUCTION_OPERATIONAL_LIMIT,
            MAX_PRODUCTION_OPERATIONAL_LIMIT,
        )

        fetch_limit = overfetch_limit(limit)

        raw_items = self._repository.fetch_order_summary(
            reference_date=reference_date,
            branch=request.branch,
            limit=fetch_limit,
        )

        items, is_complete = trim_overfetched(raw_items, limit)

        return {
            "reference_date": reference_date,
            "items": items,
            "summary": build_reference_date_summary(
                items=items,
                branch=request.branch,
                reference_date=reference_date,
                is_complete=is_complete,
            ),
            "pagination": build_operational_pagination(
                limit=limit,
                offset=0,
                returned=len(items),
                is_complete=is_complete,
            ),
        }
