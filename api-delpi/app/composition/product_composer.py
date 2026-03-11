# app/composition/product_composition.py
from app.application.use_cases.products.search_products_use_case import SearchProductsUseCase
from app.application.use_cases.products.list_product_struture_use_case import ListProductStructureUseCase

from app.infrastructure.persistence.totvs.product_repositories.product_repository import ProductRepository
from app.infrastructure.persistence.totvs.product_repositories.product_structure_repository import ProductStructureRepository


def build_search_products_use_case() -> SearchProductsUseCase:
    repository = ProductRepository()
    return SearchProductsUseCase(repository)


def build_list_structure_use_case() -> ListProductStructureUseCase:
    repository = ProductStructureRepository()
    return ListProductStructureUseCase(repository)