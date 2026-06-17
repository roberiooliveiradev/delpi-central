from app.domain.services.production.production_consumption_top_items_group_by_service import (
    ProductionConsumptionTopItemsGroupByService,
)
from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.services.production.operational_limit_page_service import (
    build_operational_pagination,
    overfetch_limit,
    trim_overfetched,
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
from app.domain.services.production.production_operational_summary_semantics_service import (
    ProductionOperationalSummarySemanticsService,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


class GetProductionConsumptionTopItemsUseCase:
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
        group_by = ProductionConsumptionTopItemsGroupByService.normalize(request.group_by)

        fetch_limit = overfetch_limit(limit)

        raw_items = self._repository.fetch_top_items(
            date_start=period_start,
            date_end_exclusive=period_end,
            branch=request.branch,
            limit=fetch_limit,
            group_by=group_by,
        )

        items, is_complete = trim_overfetched(raw_items, limit)

        return {
            "group_by": group_by,
            "items": items,
            "summary": build_period_summary(
                items=items,
                branch=request.branch,
                period_start=period_start,
                period_end_exclusive=period_end,
                is_complete=is_complete,
                consolidated_across_branches=ProductionOperationalSummarySemanticsService.consolidated_for_ranking(
                    branch=request.branch,
                    group_by=group_by,
                ),
            ),
            "pagination": build_operational_pagination(
                limit=limit,
                offset=0,
                returned=len(items),
                is_complete=is_complete,
            ),
        }
