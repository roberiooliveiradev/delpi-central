from app.application.use_cases.supplies.get_cpv_use_case import GetCPVUseCase
from app.infrastructure.persistence.totvs.supplies_repositories.cpv_query_repository import CpvQueryRepository
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import FinancialRepository
from app.application.use_cases.supplies.get_otd_use_case import GetOTDUseCase
from app.infrastructure.persistence.totvs.supplies_repositories.otd_query_repository import OtdQueryRepository
from app.application.use_cases.supplies.get_stock_value_use_case import GetStockValueUseCase
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_query_repository import StockValueQueryRepository
from app.application.use_cases.supplies.get_inventory_turnover_use_case import (
    GetInventoryTurnoverUseCase,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_turnover_query_repository import (
    InventoryTurnoverQueryRepository,
)

def build_get_cpv_use_case():
    cpv_repository = CpvQueryRepository()
    financial_repository = FinancialRepository()

    return GetCPVUseCase(
        cpv_repository=cpv_repository,
        financial_repository=financial_repository,
    )

def build_get_otd_use_case():
    repository = OtdQueryRepository()
    return GetOTDUseCase(repository)


def build_get_stock_value_use_case():
    repository = StockValueQueryRepository()
    return GetStockValueUseCase(repository)


def build_get_inventory_turnover_use_case():
    repository = InventoryTurnoverQueryRepository()
    return GetInventoryTurnoverUseCase(repository)