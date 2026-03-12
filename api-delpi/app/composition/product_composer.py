# app/composition/product_composition.py
from app.application.use_cases.products.search_products_use_case import SearchProductsUseCase
from app.application.use_cases.products.list_product_struture_use_case import ListProductStructureUseCase

from app.infrastructure.persistence.totvs.product_repositories.product_repository import ProductRepository
from app.infrastructure.persistence.totvs.product_repositories.product_structure_repository import ProductStructureRepository
from app.application.use_cases.products.export_product_structure_excel_use_case import ExportProductStructureExcelUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_parents_repository import ProductParentsRepository
from app.application.use_cases.products.list_product_parents_use_case import ListProductParentsUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_suppliers_repository import ProductSuppliersRepository
from app.application.use_cases.products.list_product_suppliers_use_case import ListProductSuppliersUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_customers_repository import ProductCustomersRepository
from app.application.use_cases.products.list_product_customers_use_case import ListProductCustomersUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_inspection_repository import ProductInspectionRepository
from app.application.use_cases.products.list_product_inspection_use_case import ListProductInspectionUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_guide_repository import ProductGuideRepository
from app.application.use_cases.products.list_product_guide_use_case import ListProductGuideUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_internal_movements_repository import ProductInternalMovementsRepository
from app.application.use_cases.products.list_product_internal_movements_use_case import ListProductInternalMovementsUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_stock_repository import ProductStockRepository
from app.application.use_cases.products.list_product_stock_use_case import ListProductStockUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_invoice_items_repository import ProductInvoiceItemsRepository
from app.application.use_cases.products.list_product_inbound_invoice_items_use_case import ListProductInboundInvoiceItemsUseCase
from app.application.use_cases.products.list_product_outbound_invoice_items_use_case import ListProductOutboundInvoiceItemsUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_purchases_repository import ProductPurchasesRepository
from app.application.use_cases.products.list_product_purchases_use_case import ListProductPurchasesUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_sales_repository import ProductSalesRepository
from app.application.use_cases.products.get_product_sales_summary_use_case import GetProductSalesSummaryUseCase



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

def build_list_product_suppliers_use_case():
    repository = ProductSuppliersRepository()
    return ListProductSuppliersUseCase(repository)

def build_list_customers_use_case():
    repository = ProductCustomersRepository()
    return ListProductCustomersUseCase(repository)

def build_list_product_inspection_use_case():
    repo = ProductInspectionRepository()
    return ListProductInspectionUseCase(repo)

def build_list_product_guide_use_case():
    repo = ProductGuideRepository()
    return ListProductGuideUseCase(repo)

def build_list_product_internal_movements_use_case():
    repo = ProductInternalMovementsRepository()
    return ListProductInternalMovementsUseCase(repo)

def build_list_product_stock_use_case():
    repo = ProductStockRepository()
    return ListProductStockUseCase(repo)

def build_list_product_inbound_invoice_items_use_case():
    repository = ProductInvoiceItemsRepository()
    return ListProductInboundInvoiceItemsUseCase(repository)

def build_list_product_outbound_invoice_items_use_case():
    repository = ProductInvoiceItemsRepository()
    return ListProductOutboundInvoiceItemsUseCase(repository)

def build_list_product_purchases():
    repository = ProductPurchasesRepository()
    return ListProductPurchasesUseCase(repository=repository)

def build_get_product_sales_summary():
    repository = ProductSalesRepository()
    return GetProductSalesSummaryUseCase(repository=repository)
