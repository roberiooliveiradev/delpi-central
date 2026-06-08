from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.services.product.product_playbook_service import (
    resolve_protheus_date,
    summarize_production,
)
from app.domain.ports.product.product_playbook_repository_port import ProductPlaybookRepositoryPort


class GetProductProductionStatusUseCase:

    DEFAULT_MAX_DEPTH = 50

    def __init__(self, repository: ProductPlaybookRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductPlaybookRequest) -> dict:
        max_depth = request.max_depth or self.DEFAULT_MAX_DEPTH
        reference_date = resolve_protheus_date(request.reference_date)

        header = self._repository.fetch_product_header(request.code)
        items = self._repository.fetch_production_status(
            request.code,
            reference_date,
            max_depth,
            branch=request.branch,
        )

        return {
            "product": header,
            "reference_date": reference_date,
            "items": items,
            "summary": summarize_production(items),
        }
