from app.domain.services.sql_query_telemetry_service import (
    get_sql_health_summary,
    query_hash,
    record_sql_query,
)


def test_record_and_summarize_sql_telemetry() -> None:
    query = "SELECT 1 AS value"

    record_sql_query(query=query, duration_ms=12.5, repository="TestRepository")
    record_sql_query(query=query, duration_ms=8.0, repository="TestRepository")

    summary = get_sql_health_summary(limit=10)

    assert summary["total_samples"] >= 2
    assert summary["top_by_count"][0]["count"] >= 2
    assert summary["top_by_count"][0]["query_hash"] == query_hash(query)
    assert summary["recent"]
