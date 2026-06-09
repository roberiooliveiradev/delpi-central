from app.composition.sql_telemetry_composer import reset_sql_telemetry_store_for_tests
from app.domain.services.sql_query_telemetry_service import (
    get_sql_health_summary,
    query_hash,
    record_sql_query,
)


def setup_function() -> None:
    reset_sql_telemetry_store_for_tests()


def test_record_and_summarize_sql_telemetry() -> None:
    query = "SELECT 1 AS value"

    record_sql_query(query=query, duration_ms=12.5, repository="TestRepository")
    record_sql_query(query=query, duration_ms=8.0, repository="TestRepository")

    summary = get_sql_health_summary(limit=10)

    assert summary["storage_backend"] == "memory"
    assert summary["total_samples"] >= 2
    assert summary["top_by_count"][0]["count"] >= 2
    assert summary["top_by_count"][0]["query_hash"] == query_hash(query)
    assert summary["by_operation_id"]
    assert summary["recent"]


def test_get_sql_health_summary_drill_down_by_operation_id() -> None:
    query = "SELECT 2 AS value"
    record_sql_query(query=query, duration_ms=5.0, repository="RepoA")
    record_sql_query(query="SELECT 3 AS value", duration_ms=7.0, repository="RepoB")

    summary = get_sql_health_summary(limit=10, operation_id="__none__")

    assert summary["filter_operation_id"] == "__none__"
    assert "timeline" in summary
    assert "queries_in_operation" in summary
