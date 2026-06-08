from si_app.application.services.hr.hr_metrics_snapshot_service import (
    HrMetricsSnapshotService,
)
from si_app.infrastructure.gateways.delpi_hr_gateway import DelpiHrGateway
from delpi_api_client import DelpiApiClient
from si_app.infrastructure.providers.strategic_indicators.hr_indicators_snapshot_provider import (
    HrIndicatorsSnapshotProvider,
)

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_hr_metrics_snapshot_service() -> HrMetricsSnapshotService:
    return HrMetricsSnapshotService(
        hr_gateway=DelpiHrGateway(_get_delpi_client()),
    )


def build_get_hr_indicators_snapshot_port() -> HrIndicatorsSnapshotProvider:
    return HrIndicatorsSnapshotProvider(
        hr_metrics_snapshot_service=build_hr_metrics_snapshot_service(),
    )
