from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshotService,
)
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from si_app.infrastructure.gateways.delpi_supplies_gateway import DelpiSuppliesGateway
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


def build_supplies_metrics_snapshot_service() -> SuppliesMetricsSnapshotService:
    client = _get_delpi_client()
    return SuppliesMetricsSnapshotService(
        supplies_gateway=DelpiSuppliesGateway(client),
        financial_gateway=DelpiFinancialGateway(client),
    )


def build_supplies_indicators_snapshot_provider() -> SuppliesIndicatorsSnapshotProvider:
    return SuppliesIndicatorsSnapshotProvider(
        supplies_metrics_snapshot_service=build_supplies_metrics_snapshot_service(),
    )
