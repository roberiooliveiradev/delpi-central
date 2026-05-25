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
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from si_app.infrastructure.gateways.delpi_supplies_gateway import (
    DelpiCpvGateway,
    DelpiInventoryTurnoverGateway,
    DelpiOtdSuppliesGateway,
    DelpiStockValueGateway,
)
from si_app.infrastructure.providers.strategic_indicators.supplies_indicators_snapshot_provider import (
    SuppliesIndicatorsSnapshotProvider,
)
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_get_cpv_use_case() -> GetCPVUseCase:
    delpi = _get_delpi_client()
    return GetCPVUseCase(
        cpv_repository=DelpiCpvGateway(delpi),
        financial_repository=DelpiFinancialGateway(delpi),
    )


def build_get_otd_use_case() -> GetOTDUseCase:
    return GetOTDUseCase(DelpiOtdSuppliesGateway(_get_delpi_client()))


def build_get_stock_value_use_case() -> GetStockValueUseCase:
    return GetStockValueUseCase(DelpiStockValueGateway(_get_delpi_client()))


def build_get_inventory_turnover_use_case() -> GetInventoryTurnoverUseCase:
    delpi = _get_delpi_client()
    return GetInventoryTurnoverUseCase(
        repository=DelpiInventoryTurnoverGateway(delpi),
        stock_repository=DelpiStockValueGateway(delpi),
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