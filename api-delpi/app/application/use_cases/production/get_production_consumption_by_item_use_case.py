from datetime import datetime, timedelta

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


class GetProductionConsumptionByItemUseCase:
    def __init__(self, repository: ProductionConsumptionRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionOperationalRequest) -> dict:
        item_code = str(request.item_code or "").strip()

        if not item_code:
            raise ValueError("Informe o código do item (path parameter code).")

        date_start, date_end_exclusive = ProtheusDateRangeService.resolve_closed_open_period(
            date_start=request.date_start,
            date_end=request.date_end,
        )
        end_inclusive = (
            datetime.strptime(date_end_exclusive, "%Y%m%d") - timedelta(days=1)
        ).strftime("%Y%m%d")
        limit = min(
            request.limit or DEFAULT_PRODUCTION_OPERATIONAL_LIMIT,
            MAX_PRODUCTION_OPERATIONAL_LIMIT,
        )

        items = self._repository.fetch_consumption_by_item(
            item_code=item_code,
            date_start=date_start,
            date_end_inclusive=end_inclusive,
            branch=request.branch,
            product_group=request.product_group,
            limit=limit,
        )

        return {
            "item_code": item_code,
            "product_group": request.product_group,
            "items": items,
            "summary": build_period_summary(
                items=items,
                branch=request.branch,
                period_start=date_start,
                period_end_exclusive=date_end_exclusive,
            ),
            "pagination": {"limit": limit, "offset": 0, "returned": len(items)},
        }
