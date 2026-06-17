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
from app.domain.ports.purchases.purchases_ranking_repository_port import (
    PurchasesRankingRepositoryPort,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


class GetPurchasesTopProductsUseCase:
    def __init__(self, repository: PurchasesRankingRepositoryPort):
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

        fetch_limit = overfetch_limit(limit)

        raw_items = self._repository.fetch_top_products(
            date_start=period_start,
            date_end_exclusive=period_end,
            branch=request.branch,
            limit=fetch_limit,
        )

        items, is_complete = trim_overfetched(raw_items, limit)

        return {
            "items": items,
            "summary": build_period_summary(
                items=items,
                branch=request.branch,
                period_start=period_start,
                period_end_exclusive=period_end,
                is_complete=is_complete,
            ),
            "pagination": build_operational_pagination(
                limit=limit,
                offset=0,
                returned=len(items),
                is_complete=is_complete,
            ),
        }
