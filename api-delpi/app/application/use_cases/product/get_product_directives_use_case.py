from app.application.dto.product.product_directives_request import ProductDirectivesRequest
from app.application.services.product.product_directives_service import (
    build_product_directives_payload,
    extract_raw_material_codes,
    resolve_product_identifier,
)
from app.domain.ports.product.product_playbook_repository_port import ProductPlaybookRepositoryPort
from app.domain.ports.product.product_query_repository_port import ProductQueryRepositoryPort
from app.domain.ports.product.product_raw_material_price_repository_port import (
    ProductRawMaterialPriceRepositoryPort,
)
from app.domain.ports.product.product_suppliers_repository_port import ProductSuppliersRepositoryPort


class GetProductDirectivesUseCase:

    DEFAULT_MAX_DEPTH = 50

    def __init__(
        self,
        product_repository: ProductQueryRepositoryPort,
        playbook_repository: ProductPlaybookRepositoryPort,
        suppliers_repository: ProductSuppliersRepositoryPort,
        price_repository: ProductRawMaterialPriceRepositoryPort,
    ):
        self._product_repository = product_repository
        self._playbook_repository = playbook_repository
        self._suppliers_repository = suppliers_repository
        self._price_repository = price_repository

    def execute(self, request: ProductDirectivesRequest) -> dict:
        resolved = resolve_product_identifier(
            request.identifier,
            fetch_by_code=self._product_repository.fetch_product_by_code,
            fetch_by_customer_reference=self._product_repository.fetch_product_by_customer_reference,
        )

        if not resolved:
            return {"resolution": None, "product": None, "structure": None, "raw_materials": [], "summary": None}

        max_depth = request.max_depth or self.DEFAULT_MAX_DEPTH
        structure_items = self._playbook_repository.fetch_structure_with_exclusivity(
            resolved.product_code,
            max_depth,
        )
        raw_material_codes = extract_raw_material_codes(structure_items)

        suppliers_rows = self._suppliers_repository.list_suppliers_for_codes(raw_material_codes)
        last_purchase_rows = self._price_repository.fetch_last_purchases_for_codes(
            raw_material_codes,
            branch=request.branch,
        )

        return build_product_directives_payload(
            resolved=resolved,
            structure_items=structure_items,
            suppliers_rows=suppliers_rows,
            last_purchase_rows=last_purchase_rows,
        )
