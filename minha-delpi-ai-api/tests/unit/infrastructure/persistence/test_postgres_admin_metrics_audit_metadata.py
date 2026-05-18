from app.infrastructure.persistence.postgres_admin_metrics_repository import (
    PostgresAdminMetricsRepository,
)


def test_metric_number_from_metadata_reads_dict():
    repository = PostgresAdminMetricsRepository()

    assert repository._metric_number_from_metadata({"latency_ms": 120}, "latency_ms") == 120.0
    assert repository._metric_number_from_metadata(None, "latency_ms") == 0.0
