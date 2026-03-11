# app/application/use_cases/products/list_product_suppliers_use_case.py
from app.domain.ports.product_suppliers_repository_port import ProductSuppliersRepositoryPort
from app.application.dto.list_product_suppliers_request import ListProductSuppliersRequest


class ListProductSuppliersUseCase:

    def __init__(self, repository: ProductSuppliersRepositoryPort):
        self._repository = repository


    def execute(self, request: ListProductSuppliersRequest):

        return self._repository.list_suppliers(
            request.code,
            request.page,
            request.page_size
        )