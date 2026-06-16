# app/composition/product_composition.py
from app.application.use_cases.product.search_products_use_case import SearchProductsUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_repository import ProductRepository
from app.infrastructure.persistence.totvs.product_repositories.product_structure_repository import ProductStructureRepository
from app.application.use_cases.product.list_product_structure_use_case import ListProductStructureUseCase
from app.application.use_cases.product.export_product_structure_excel_use_case import ExportProductStructureExcelUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_parents_repository import ProductParentsRepository
from app.application.use_cases.product.list_product_parents_use_case import ListProductParentsUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_suppliers_repository import ProductSuppliersRepository
from app.application.use_cases.product.list_product_suppliers_use_case import ListProductSuppliersUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_customers_repository import ProductCustomersRepository
from app.application.use_cases.product.list_product_customers_use_case import ListProductCustomersUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_inspection_repository import ProductInspectionRepository
from app.application.use_cases.product.list_product_inspection_use_case import ListProductInspectionUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_guide_repository import ProductGuideRepository
from app.application.use_cases.product.list_product_guide_use_case import ListProductGuideUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_internal_movements_repository import ProductInternalMovementsRepository
from app.application.use_cases.product.list_product_internal_movements_use_case import ListProductInternalMovementsUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_stock_repository import ProductStockRepository
from app.application.use_cases.product.list_product_stock_use_case import ListProductStockUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_invoice_items_repository import ProductInvoiceItemsRepository
from app.application.use_cases.product.list_product_inbound_invoice_items_use_case import ListProductInboundInvoiceItemsUseCase
from app.application.use_cases.product.list_product_outbound_invoice_items_use_case import ListProductOutboundInvoiceItemsUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_purchases_repository import ProductPurchasesRepository
from app.application.use_cases.product.list_product_purchases_use_case import ListProductPurchasesUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_sales_repository import ProductSalesRepository
from app.application.use_cases.product.get_product_sales_summary_use_case import GetProductSalesSummaryUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_sales_open_orders_repository import ProductSalesOpenOrdersRepository
from app.application.use_cases.product.get_product_sales_open_orders_use_case import GetProductSalesOpenOrdersUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_sales_billing_repository import ProductSalesBillingRepository
from app.application.use_cases.product.get_product_sales_billing_use_case import GetProductSalesBillingUseCase
from app.infrastructure.persistence.totvs.product_repositories.product_pricing_repository import ProductPricingRepository
from app.application.use_cases.product.get_product_pricing_use_case import GetProductPricingUseCase
from app.application.use_cases.product.product_analyser_use_case import ProductAnalyserUseCase
from app.application.use_cases.product.list_exclusive_raw_materials_catalog_use_case import (
    ListExclusiveRawMaterialsCatalogUseCase,
)
from app.infrastructure.persistence.totvs.product_repositories.product_exclusive_raw_material_repository import (
    ProductExclusiveRawMaterialRepository,
)
from app.infrastructure.persistence.totvs.product_repositories.product_playbook_repository import (
    ProductPlaybookRepository,
)
from app.application.use_cases.product.get_product_structure_exclusivity_use_case import (
    GetProductStructureExclusivityUseCase,
)
from app.application.use_cases.product.get_product_production_status_use_case import (
    GetProductProductionStatusUseCase,
)
from app.application.use_cases.product.get_product_shipping_status_use_case import (
    GetProductShippingStatusUseCase,
)
from app.application.use_cases.product.get_product_factory_status_use_case import (
    GetProductFactoryStatusUseCase,
)
from app.application.use_cases.product.get_product_cost_impact_simulation_use_case import (
    GetProductCostImpactSimulationUseCase,
)
from app.application.use_cases.product.get_product_raw_material_price_use_cases import (
    GetProductLastPurchaseUseCase,
    GetProductPurchaseBudgetHistoryUseCase,
    GetProductPurchasePriceHistoryUseCase,
    GetProductRawMaterialPriceIntelligenceUseCase,
)
from app.application.use_cases.product.get_product_directives_use_case import (
    GetProductDirectivesUseCase,
)
from app.infrastructure.persistence.totvs.product_repositories.product_cost_impact_repository import (
    ProductCostImpactRepository,
)
from app.infrastructure.persistence.totvs.product_repositories.product_raw_material_price_repository import (
    ProductRawMaterialPriceRepository,
)



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

def build_get_product_sales_open_orders():
    repository = ProductSalesOpenOrdersRepository()
    return GetProductSalesOpenOrdersUseCase(repository=repository)

def build_get_product_sales_billing():
    repository = ProductSalesBillingRepository()
    return GetProductSalesBillingUseCase(repository=repository)

def build_get_product_pricing():
    repository = ProductPricingRepository()
    return GetProductPricingUseCase(repository=repository)

def build_product_analyser_use_case():

    return ProductAnalyserUseCase(
        build_search_products_use_case(),
        build_list_structure_use_case(),
        build_list_product_guide_use_case(),
        build_list_product_inspection_use_case()
    )


def build_get_product_structure_exclusivity_use_case() -> GetProductStructureExclusivityUseCase:
    return GetProductStructureExclusivityUseCase(ProductPlaybookRepository())


def build_get_product_production_status_use_case() -> GetProductProductionStatusUseCase:
    return GetProductProductionStatusUseCase(ProductPlaybookRepository())


def build_get_product_shipping_status_use_case() -> GetProductShippingStatusUseCase:
    return GetProductShippingStatusUseCase(ProductPlaybookRepository())


def build_get_product_factory_status_use_case() -> GetProductFactoryStatusUseCase:
    return GetProductFactoryStatusUseCase(ProductPlaybookRepository())


def build_get_product_cost_impact_simulation_use_case() -> GetProductCostImpactSimulationUseCase:
    return GetProductCostImpactSimulationUseCase(ProductCostImpactRepository())


def build_get_product_last_purchase_use_case() -> GetProductLastPurchaseUseCase:
    return GetProductLastPurchaseUseCase(ProductRawMaterialPriceRepository())


def build_get_product_purchase_price_history_use_case() -> GetProductPurchasePriceHistoryUseCase:
    return GetProductPurchasePriceHistoryUseCase(ProductRawMaterialPriceRepository())


def build_get_product_purchase_budget_history_use_case() -> GetProductPurchaseBudgetHistoryUseCase:
    return GetProductPurchaseBudgetHistoryUseCase(ProductRawMaterialPriceRepository())


def build_get_product_raw_material_price_intelligence_use_case() -> (
    GetProductRawMaterialPriceIntelligenceUseCase
):
    return GetProductRawMaterialPriceIntelligenceUseCase(ProductRawMaterialPriceRepository())


def build_list_exclusive_raw_materials_catalog_use_case() -> (
    ListExclusiveRawMaterialsCatalogUseCase
):
    return ListExclusiveRawMaterialsCatalogUseCase(ProductExclusiveRawMaterialRepository())


def build_get_product_directives_use_case() -> GetProductDirectivesUseCase:
    return GetProductDirectivesUseCase(
        product_repository=ProductRepository(),
        playbook_repository=ProductPlaybookRepository(),
        suppliers_repository=ProductSuppliersRepository(),
        price_repository=ProductRawMaterialPriceRepository(),
    )