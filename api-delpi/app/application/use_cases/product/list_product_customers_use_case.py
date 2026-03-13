# app/application/use_cases/products/list_product_customers_use_case.py

from app.domain.ports.product.product_customers_repository_port import ProductCustomersRepositoryPort
from app.application.dto.product.list_product_customers_request import ListProductCustomersRequest
from app.application.models.page import Page
from app.domain.entities.product.customer import Customer


class ListProductCustomersUseCase:

    def __init__(self, repository: ProductCustomersRepositoryPort):
        self._repository = repository

    def execute(self, request: ListProductCustomersRequest) -> Page[Customer]:

        page = request.page or 1
        page_size = request.page_size or 50

        return self._repository.list_customers(
            request.code,
            page,
            page_size
        )