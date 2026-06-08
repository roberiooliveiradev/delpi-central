from si_app.application.services.production.production_metrics_snapshot_service import (
    ProductionMetricsSnapshotService,
)
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from si_app.infrastructure.gateways.delpi_production_gateway import (
    DelpiProductionGateway,
    DelpiProductionSheetsGateway,
)
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_production_metrics_snapshot_service() -> ProductionMetricsSnapshotService:
    delpi = _get_delpi_client()

    return ProductionMetricsSnapshotService(
        production_sheets_gateway=DelpiProductionSheetsGateway(delpi),
        production_gateway=DelpiProductionGateway(delpi),
        financial_gateway=DelpiFinancialGateway(delpi),
    )
