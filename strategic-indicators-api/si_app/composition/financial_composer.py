from si_app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from si_app.infrastructure.gateways.delpi_financial_gateway import (
    DelpiFinancialGateway,
    DelpiFinancialSheetsGateway,
)
from delpi_api_client import DelpiApiClient
from si_app.infrastructure.providers.strategic_indicators.financial_indicators_snapshot_provider import (
    FinancialIndicatorsSnapshotProvider,
)

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_financial_metrics_snapshot_service() -> FinancialMetricsSnapshotService:
    client = _get_delpi_client()
    return FinancialMetricsSnapshotService(
        financial_sheets_gateway=DelpiFinancialSheetsGateway(client),
        financial_gateway=DelpiFinancialGateway(client),
    )


def build_get_financial_indicators_snapshot_port() -> FinancialIndicatorsSnapshotProvider:
    return FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=build_financial_metrics_snapshot_service(),
    )
