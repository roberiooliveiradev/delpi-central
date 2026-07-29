from datetime import datetime, timedelta

from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.services.product.product_playbook_service import (
    resolve_exclusive_end_date,
    resolve_protheus_date,
    summarize_shipping,
)
from app.application.use_cases.production_appointments.get_produced_quantity_use_case import (
    GetProducedQuantityUseCase,
)
from app.domain.ports.product.product_playbook_repository_port import (
    ProductPlaybookRepositoryPort,
)
from app.domain.production.production_appointments.production_appointments_scope import (
    SHIPPING_PRODUCED_PRODUCT_TYPES,
)


class GetProductShippingStatusUseCase:

    def __init__(
        self,
        repository: ProductPlaybookRepositoryPort,
        produced_quantity_use_case: GetProducedQuantityUseCase,
    ):
        self._repository = repository
        self._produced_quantity = produced_quantity_use_case

    def execute(self, request: ProductPlaybookRequest) -> dict:
        date_start = resolve_protheus_date(request.date_start or request.reference_date)
        date_end_exclusive = resolve_exclusive_end_date(request.date_end, date_start)
        end_inclusive = (
            datetime.strptime(date_end_exclusive, "%Y%m%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        start_iso = datetime.strptime(date_start, "%Y%m%d").strftime("%Y-%m-%d")

        header = self._repository.fetch_product_header(request.code)
        items = self._produced_quantity.list_detail(
            date_start=start_iso,
            date_end=end_inclusive,
            branch=request.branch,
            product=request.code,
            product_types=sorted(SHIPPING_PRODUCED_PRODUCT_TYPES),
        )

        return {
            "product": header,
            "start_date": date_start,
            "date_end_exclusive": date_end_exclusive,
            "items": items,
            "summary": summarize_shipping(items),
        }
