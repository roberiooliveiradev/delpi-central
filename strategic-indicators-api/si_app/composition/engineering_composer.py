from __future__ import annotations

from si_app.application.services.engineering.engineering_metrics_snapshot_service import (
    EngineeringMetricsSnapshotService,
)
from si_app.infrastructure.gateways.delpi_engineering_gateway import DelpiEngineeringGateway
from delpi_api_client import DelpiApiClient

_delpi_client: DelpiApiClient | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient()
    return _delpi_client


def build_engineering_metrics_snapshot_service() -> EngineeringMetricsSnapshotService:
    return EngineeringMetricsSnapshotService(
        engineering_gateway=DelpiEngineeringGateway(_get_delpi_client()),
    )


def build_engineering_indicators_snapshot_provider():
    from si_app.infrastructure.providers.strategic_indicators.engineering_indicators_snapshot_provider import (
        EngineeringIndicatorsSnapshotProvider,
    )

    return EngineeringIndicatorsSnapshotProvider(
        engineering_metrics_snapshot_service=build_engineering_metrics_snapshot_service(),
    )
