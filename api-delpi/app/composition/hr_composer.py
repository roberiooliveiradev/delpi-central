from app.application.services.hr.hr_metrics_snapshot_service import (
    HrMetricsSnapshotService,
)
from app.infrastructure.persistence.portal_rh.hr_repositories.hr_metrics_repository import (
    HrMetricsRepository,
)
def build_hr_metrics_repository() -> HrMetricsRepository:
    return HrMetricsRepository()


def build_hr_metrics_snapshot_service() -> HrMetricsSnapshotService:
    return HrMetricsSnapshotService(
        repository=build_hr_metrics_repository(),
    )

