# app/application/use_cases/products/list_product_stock_use_case.py

from app.application.dto.product.list_product_stock_request import ListProductStockRequest
from app.application.services.product.product_stock_cache import (
    get_cached_product_stock,
    product_stock_cache_key,
    set_cached_product_stock,
)
from app.domain.ports.product.product_stock_repository_port import ProductStockRepositoryPort


class ListProductStockUseCase:

    def __init__(self, repository: ProductStockRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductStockRequest):
        cache_key = product_stock_cache_key(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size,
            branch=dto.branch,
            location=dto.location,
        )
        cached = get_cached_product_stock(cache_key)

        if cached is not None:
            return cached

        page = self.repository.list_stock(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size,
            branch=dto.branch,
            location=dto.location,
        )
        payload = page.to_dict()
        set_cached_product_stock(cache_key, payload)
        return payload
