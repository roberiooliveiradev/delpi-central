from app.domain.ports.admin_metrics_repository_port import AdminMetricsRepositoryPort
from app.infrastructure.config.settings import Settings


class GetAdminMetricsSummaryUseCase:
    def __init__(self, metrics_repository: AdminMetricsRepositoryPort):
        self.metrics_repository = metrics_repository

    def execute(self, *, hours: int = 24) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        return self.metrics_repository.get_summary(hours=safe_hours)

    def execute_timeseries(self, *, hours: int = 168, bucket_hours: int = 24) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        safe_bucket = max(1, min(int(bucket_hours), safe_hours))
        return self.metrics_repository.get_timeseries(
            hours=safe_hours,
            bucket_hours=safe_bucket,
        )
