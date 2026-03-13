# app/application/use_cases/products/search_products_use_case.py
from app.application.models.page import Page
from app.domain.entities.product.product import Product
from app.application.dto.product.list_products_requests import ListProductsRequest
from app.domain.ports.product.product_query_repository_port import ProductQueryRepositoryPort


class SearchProductsUseCase:
    def __init__(self, repository: ProductQueryRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: ListProductsRequest
    ) -> Page[Product]:
        return self._repository.search_products(
           code= request.code,
           description = request.description,
           group=request.group_code,
           page = request.page,
           page_size = request.page_size,
           sort=request.sort,
           direction=request.direction,
        )
    

