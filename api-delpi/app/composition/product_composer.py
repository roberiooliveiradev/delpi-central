# app/composition/product_composition.py
from app.application.use_cases.products.search_products_use_case import (
    SearchProductsUseCase,
)
from app.infrastructure.persistence.totvs.product_repositories.product_repository import ProductRepository


def build_search_products_use_case() -> SearchProductsUseCase:
    repository = ProductRepository()
    return SearchProductsUseCase(repository)

