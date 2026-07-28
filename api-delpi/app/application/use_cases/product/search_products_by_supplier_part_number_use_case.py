# app/application/use_cases/product/search_products_by_supplier_part_number_use_case.py
from app.application.dto.product.search_products_by_supplier_part_number_request import (
    SearchProductsBySupplierPartNumberRequest,
)
from app.domain.ports.product.product_suppliers_repository_port import (
    ProductSuppliersRepositoryPort,
)


class SearchProductsBySupplierPartNumberUseCase:
    def __init__(self, repository: ProductSuppliersRepositoryPort):
        self._repository = repository

    def execute(self, request: SearchProductsBySupplierPartNumberRequest):
        return self._repository.search_by_supplier_part_number(
            request.supplier_part_number,
            supplier_code=request.supplier_code,
            page=request.page,
            page_size=request.page_size,
        )
