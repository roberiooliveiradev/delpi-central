from app.domain.ports.admin_metrics_repository_port import AdminMetricsRepositoryPort


class GetAdminMetricsSummaryUseCase:
    def __init__(self, metrics_repository: AdminMetricsRepositoryPort):
        self.metrics_repository = metrics_repository

    def execute(self) -> dict:
        return self.metrics_repository.get_summary()
