from app.config import settings

from app.application.use_cases.supplies.get_negotiation_savings_summary_use_case import (
    GetNegotiationSavingsSummaryUseCase,
)
from app.application.use_cases.supplies.get_cpv_use_case import GetCPVUseCase
from app.application.use_cases.supplies.get_inventory_turnover_use_case import (
    GetInventoryTurnoverUseCase,
)
from app.application.use_cases.supplies.get_otd_use_case import GetOTDUseCase
from app.application.use_cases.supplies.get_stock_value_use_case import (
    GetStockValueUseCase,
)
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.cpv_query_repository import (
    CpvQueryRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_turnover_query_repository import (
    InventoryTurnoverQueryRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.otd_query_repository import (
    OtdQueryRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_query_repository import (
    StockValueQueryRepository,
)
from app.infrastructure.persistence.google_sheets.supplies.negotiation_savings_repository import (
    NegotiationSavingsRepository,
)
from app.application.use_cases.supplies.get_safety_stock_filters_use_case import (
    GetSafetyStockFiltersUseCase,
)
from app.application.use_cases.supplies.get_safety_stock_item_details_use_case import (
    GetSafetyStockItemDetailsUseCase,
)
from app.application.use_cases.supplies.get_safety_stock_item_suppliers_use_case import (
    GetSafetyStockItemSuppliersUseCase,
)
from app.application.use_cases.supplies.get_safety_stock_items_use_case import (
    GetSafetyStockItemsUseCase,
)
from app.application.use_cases.supplies.get_safety_stock_summary_use_case import (
    GetSafetyStockSummaryUseCase,
)
from app.application.use_cases.supplies.get_safety_stock_supplier_price_history_use_case import (
    GetSafetyStockSupplierPriceHistoryUseCase,
)
from app.infrastructure.persistence.totvs.product_repositories.product_raw_material_price_repository import (
    ProductRawMaterialPriceRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_query_repository import (
    SafetyStockQueryRepository,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)


def _build_google_sheets_client() -> GoogleSheetsClient:
    return GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT or 10))


def _validate_supplies_negotiation_sheet_config() -> tuple[str, str]:
    sheet_id = (settings.SUPPLIES_IDD_SHEET_ID or "").strip()
    gid = (settings.SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID or "").strip()

    if not sheet_id or not gid:
        raise ValueError(
            "Planilha de economia em negociações não configurada. "
            "Defina SUPPLIES_IDD_SHEET_ID e SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID "
            "em infra/.env e recrie o container api-delpi "
            "(docker compose up -d --force-recreate api-delpi)."
        )

    return sheet_id, gid


def _build_negotiation_savings_repository() -> NegotiationSavingsRepository:
    sheet_id, gid = _validate_supplies_negotiation_sheet_config()
    return NegotiationSavingsRepository(
        client=_build_google_sheets_client(),
        sheet_id=sheet_id,
        gid=gid,
        utils=Utils(),
    )
def build_get_cpv_use_case() -> GetCPVUseCase:
    cpv_repository = CpvQueryRepository()
    financial_repository = FinancialRepository()

    return GetCPVUseCase(
        cpv_repository=cpv_repository,
        financial_repository=financial_repository,
    )


def build_get_otd_use_case() -> GetOTDUseCase:
    repository = OtdQueryRepository()
    return GetOTDUseCase(repository)


def build_get_stock_value_use_case() -> GetStockValueUseCase:
    repository = StockValueQueryRepository()
    return GetStockValueUseCase(repository)


def build_get_inventory_turnover_use_case() -> GetInventoryTurnoverUseCase:
    return GetInventoryTurnoverUseCase(
        repository=InventoryTurnoverQueryRepository(),
        stock_repository=StockValueQueryRepository(),
    )


def build_get_negotiation_savings_summary_use_case() -> GetNegotiationSavingsSummaryUseCase:
    return GetNegotiationSavingsSummaryUseCase(
        repository=_build_negotiation_savings_repository(),
    )


def build_get_safety_stock_filters_use_case() -> GetSafetyStockFiltersUseCase:
    return GetSafetyStockFiltersUseCase(repository=SafetyStockQueryRepository())


def build_get_safety_stock_summary_use_case() -> GetSafetyStockSummaryUseCase:
    return GetSafetyStockSummaryUseCase(repository=SafetyStockQueryRepository())


def build_get_safety_stock_items_use_case() -> GetSafetyStockItemsUseCase:
    return GetSafetyStockItemsUseCase(repository=SafetyStockQueryRepository())


def build_get_safety_stock_item_details_use_case() -> GetSafetyStockItemDetailsUseCase:
    return GetSafetyStockItemDetailsUseCase(repository=SafetyStockQueryRepository())


def build_get_safety_stock_item_suppliers_use_case() -> GetSafetyStockItemSuppliersUseCase:
    return GetSafetyStockItemSuppliersUseCase(repository=SafetyStockQueryRepository())


def build_get_safety_stock_supplier_price_history_use_case() -> (
    GetSafetyStockSupplierPriceHistoryUseCase
):
    return GetSafetyStockSupplierPriceHistoryUseCase(
        repository=ProductRawMaterialPriceRepository()
    )