from app.domain.services.sql_health_aggregator import (
    build_sql_health_payload,
    filter_entries_by_operation_id,
)
from app.domain.services.sql_query_telemetry_models import SqlQueryRecord


def _record(**overrides) -> SqlQueryRecord:
    payload = {
        "query_hash": "hash-a",
        "duration_ms": 10.0,
        "operation_id": "get_ppm_internal_summary",
        "caller_app": "api-delpi-console",
        "repository": "PpmRepository",
        "recorded_at": "2026-06-09T12:00:00+00:00",
        "preview": "SELECT 1",
    }
    payload.update(overrides)
    return SqlQueryRecord(**payload)


def test_build_sql_health_payload_groups_by_operation_id() -> None:
    entries = [
        _record(query_hash="hash-a", duration_ms=20, operation_id="get_ppm_internal_summary"),
        _record(query_hash="hash-b", duration_ms=40, operation_id="get_ppm_external_summary"),
        _record(query_hash="hash-a", duration_ms=30, operation_id="get_ppm_internal_summary"),
    ]

    payload = build_sql_health_payload(entries, limit=10, storage_backend="memory")

    assert payload["total_samples"] == 3
    assert len(payload["by_operation_id"]) == 2
    assert payload["by_operation_id"][0]["operation_id"] == "get_ppm_internal_summary"
    assert payload["by_operation_id"][0]["count"] == 2
    assert payload["by_operation_id"][0]["query_count"] == 1


def test_filter_entries_by_operation_id_and_drill_down() -> None:
    entries = [
        _record(query_hash="hash-a", operation_id="get_ppm_internal_summary"),
        _record(query_hash="hash-b", operation_id="get_ppm_external_summary"),
        _record(query_hash="hash-a", operation_id=None),
    ]

    filtered = filter_entries_by_operation_id(entries, "get_ppm_internal_summary")
    payload = build_sql_health_payload(
        filtered,
        limit=10,
        storage_backend="memory",
        filter_operation_id="get_ppm_internal_summary",
    )

    assert payload["filter_operation_id"] == "get_ppm_internal_summary"
    assert payload["total_samples"] == 1
    assert len(payload["timeline"]) == 1
    assert payload["queries_in_operation"][0]["query_hash"] == "hash-a"


def test_filter_entries_without_operation_id() -> None:
    entries = [
        _record(operation_id="get_ppm_internal_summary"),
        _record(operation_id=None, query_hash="hash-none"),
    ]

    filtered = filter_entries_by_operation_id(entries, "__none__")
    assert len(filtered) == 1
    assert filtered[0].query_hash == "hash-none"
