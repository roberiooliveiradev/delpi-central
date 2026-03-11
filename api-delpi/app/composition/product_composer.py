# app/composition/product_composition.py
from app.application.use_cases.products.search_products_use_case import SearchProductsUseCase
from app.application.use_cases.products.list_product_struture_use_case import ListProductStructureUseCase

from app.infrastructure.persistence.totvs.product_repositories.product_repository import ProductRepository
from app.infrastructure.persistence.totvs.product_repositories.product_structure_repository import ProductStructureRepository
from app.application.use_cases.products.export_product_structure_excel_use_case import ExportProductStructureExcelUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_parents_repository import ProductParentsRepository
from app.application.use_cases.products.list_product_parents_use_case import ListProductParentsUseCase


def build_search_products_use_case() -> SearchProductsUseCase:
    repository = ProductRepository()
    return SearchProductsUseCase(repository)


def build_list_structure_use_case() -> ListProductStructureUseCase:
    repository = ProductStructureRepository()
    return ListProductStructureUseCase(repository)


def build_export_structure_excel_use_case():
    repository = ProductStructureRepository()
    return ExportProductStructureExcelUseCase(repository)

def build_list_parents_use_case():
    repository = ProductParentsRepository()
    return ListProductParentsUseCase(repository)