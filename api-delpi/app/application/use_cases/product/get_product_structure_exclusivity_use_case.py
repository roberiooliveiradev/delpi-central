from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.services.product.product_playbook_service import summarize_structure
from app.domain.ports.product.product_playbook_repository_port import ProductPlaybookRepositoryPort


class GetProductStructureExclusivityUseCase:

    DEFAULT_MAX_DEPTH = 50

    def __init__(self, repository: ProductPlaybookRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductPlaybookRequest) -> dict:
        max_depth = request.max_depth or self.DEFAULT_MAX_DEPTH
        header = self._repository.fetch_product_header(request.code)
        items = self._repository.fetch_structure_with_exclusivity(request.code, max_depth)

        return {
            "product": header,
            "items": items,
            "summary": summarize_structure(items),
        }
