from si_app.application.services.commercial.commercial_metrics_snapshot_service import (
    CommercialMetricsSnapshotService,
    DEFAULT_BRANCH_TARGET,
    DEFAULT_HEAD_OFFICE_TARGET,
)
from si_app.infrastructure.gateways.delpi_commercial_gateway import DelpiCommercialGateway
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from si_app.infrastructure.providers.strategic_indicators.commercial_indicators_snapshot_provider import (
    CommercialIndicatorsSnapshotProvider,
)
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_commercial_metrics_snapshot_service() -> CommercialMetricsSnapshotService:
    client = _get_delpi_client()
    return CommercialMetricsSnapshotService(
        commercial_gateway=DelpiCommercialGateway(client),
        financial_gateway=DelpiFinancialGateway(client),
        head_office_target=DEFAULT_HEAD_OFFICE_TARGET,
        branch_target=DEFAULT_BRANCH_TARGET,
    )


def build_commercial_indicators_snapshot_provider() -> CommercialIndicatorsSnapshotProvider:
    return CommercialIndicatorsSnapshotProvider(
        commercial_metrics_snapshot_service=build_commercial_metrics_snapshot_service(),
    )
