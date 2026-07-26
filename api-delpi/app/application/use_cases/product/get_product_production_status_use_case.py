from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.services.product.product_playbook_service import (
    apply_pa_bom_reference_to_production_items,
    attach_pa_reference,
    resolve_exclusive_end_date,
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
        date_start = resolve_protheus_date(request.date_start or request.reference_date)
        date_end_exclusive = resolve_exclusive_end_date(request.date_end, date_start)

        header = self._repository.fetch_product_header(request.code)
        items = self._repository.fetch_production_status(
            request.code,
            reference_date,
            max_depth,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.branch,
        )
        product_unit = str((header or {}).get("unit") or "").strip() or None
        items = apply_pa_bom_reference_to_production_items(items, product_unit)

        return attach_pa_reference(
            {
            "product": header,
            "reference_date": reference_date,
            "start_date": date_start,
            "date_end_exclusive": date_end_exclusive,
            "items": items,
            "summary": summarize_production(items),
        },
            header,
        )
