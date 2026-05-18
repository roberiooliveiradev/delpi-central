from app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshotService,
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
    repository = InventoryTurnoverQueryRepository()
    return GetInventoryTurnoverUseCase(repository)


def build_supplies_metrics_snapshot_service() -> SuppliesMetricsSnapshotService:
    return SuppliesMetricsSnapshotService(
        get_cpv_use_case=build_get_cpv_use_case(),
        get_inventory_turnover_use_case=build_get_inventory_turnover_use_case(),
        get_otd_use_case=build_get_otd_use_case(),
        get_stock_value_use_case=build_get_stock_value_use_case(),
    )