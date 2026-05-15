from si_app.application.services.hr.hr_metrics_snapshot_service import (
    HrMetricsSnapshotService,
)
from si_app.infrastructure.persistence.portal_rh.hr_repositories.hr_metrics_repository import (
    HrMetricsRepository,
)
from si_app.infrastructure.providers.strategic_indicators.hr_indicators_snapshot_provider import (
    HrIndicatorsSnapshotProvider,
)


def build_hr_metrics_repository() -> HrMetricsRepository:
    return HrMetricsRepository()


def build_hr_metrics_snapshot_service() -> HrMetricsSnapshotService:
    return HrMetricsSnapshotService(
        repository=build_hr_metrics_repository(),
    )


def build_get_hr_indicators_snapshot_port() -> HrIndicatorsSnapshotProvider:
    return HrIndicatorsSnapshotProvider(
        hr_metrics_snapshot_service=build_hr_metrics_snapshot_service(),
    )