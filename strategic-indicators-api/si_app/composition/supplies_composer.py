from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshotService,
)
from si_app.application.use_cases.supplies.get_cpv_use_case import GetCPVUseCase
from si_app.application.use_cases.supplies.get_inventory_turnover_use_case import (
    GetInventoryTurnoverUseCase,
)
from si_app.application.use_cases.supplies.get_otd_use_case import GetOTDUseCase
from si_app.application.use_cases.supplies.get_stock_value_use_case import (
    GetStockValueUseCase,
)
from si_app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)
from si_app.infrastructure.persistence.totvs.supplies_repositories.cpv_query_repository import (
    CpvQueryRepository,
)
from si_app.infrastructure.persistence.totvs.supplies_repositories.inventory_turnover_query_repository import (
    InventoryTurnoverQueryRepository,
)
from si_app.infrastructure.persistence.totvs.supplies_repositories.otd_query_repository import (
    OtdQueryRepository,
)
from si_app.infrastructure.persistence.totvs.supplies_repositories.stock_value_query_repository import (
    StockValueQueryRepository,
)
from si_app.infrastructure.providers.strategic_indicators.supplies_indicators_snapshot_provider import (
    SuppliesIndicatorsSnapshotProvider,
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


def build_supplies_metrics_snapshot_service() -> SuppliesMetricsSnapshotService:
    return SuppliesMetricsSnapshotService(
        get_cpv_use_case=build_get_cpv_use_case(),
        get_inventory_turnover_use_case=build_get_inventory_turnover_use_case(),
        get_otd_use_case=build_get_otd_use_case(),
        get_stock_value_use_case=build_get_stock_value_use_case(),
    )


def build_supplies_indicators_snapshot_provider() -> SuppliesIndicatorsSnapshotProvider:
    return SuppliesIndicatorsSnapshotProvider(
        supplies_metrics_snapshot_service=build_supplies_metrics_snapshot_service(),
    )