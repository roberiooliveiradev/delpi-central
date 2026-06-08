from si_app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from si_app.infrastructure.gateways.delpi_quality_gateway import DelpiQualityGateway
from si_app.infrastructure.providers.strategic_indicators.quality_indicators_snapshot_provider import (
    QualityIndicatorsSnapshotProvider,
)
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_quality_metrics_snapshot_service() -> QualityMetricsSnapshotService:
    return QualityMetricsSnapshotService(
        quality_gateway=DelpiQualityGateway(_get_delpi_client()),
    )


def build_get_quality_indicators_snapshot_port() -> QualityIndicatorsSnapshotProvider:
    return QualityIndicatorsSnapshotProvider(
        quality_metrics_snapshot_service=build_quality_metrics_snapshot_service(),
    )
