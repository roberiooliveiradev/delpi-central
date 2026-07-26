from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.services.product.product_playbook_service import (
    resolve_exclusive_end_date,
    resolve_protheus_date,
    summarize_shipping,
)
from app.domain.ports.product.product_playbook_repository_port import ProductPlaybookRepositoryPort


class GetProductShippingStatusUseCase:

    def __init__(self, repository: ProductPlaybookRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductPlaybookRequest) -> dict:
        date_start = resolve_protheus_date(request.date_start or request.reference_date)
        date_end_exclusive = resolve_exclusive_end_date(request.date_end, date_start)

        header = self._repository.fetch_product_header(request.code)
        items = self._repository.fetch_shipping_status(
            request.code,
            date_start,
            date_end_exclusive,
            branch=request.branch,
        )

        return {
            "product": header,
            "start_date": date_start,
            "date_end_exclusive": date_end_exclusive,
            "items": items,
            "summary": summarize_shipping(items),
        }
