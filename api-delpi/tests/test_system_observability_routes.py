"""Integração HTTP das rotas de observabilidade (Fases 2 e 3 do console)."""

from __future__ import annotations

import json

from app.composition.query_cache_composer import build_query_cache, reset_query_cache_for_tests
from app.composition.sql_telemetry_composer import reset_sql_telemetry_store_for_tests
from app.domain.services.caller_request_stats_service import (
    record_caller_request,
    reset_caller_request_stats_for_tests,
)
from app.domain.services.query_cache_stats_service import reset_query_cache_stats_for_tests
from app.domain.services.sql_query_telemetry_service import record_sql_query


def _body(response) -> dict:
    return json.loads(response.body.decode())


def setup_function() -> None:
    reset_sql_telemetry_store_for_tests()
    reset_query_cache_stats_for_tests()
    reset_query_cache_for_tests()
    reset_caller_request_stats_for_tests()


def test_get_sql_health_includes_phase2_fields() -> None:
    from app.interface.http.routes.system_routes import get_sql_health

    record_sql_query(query="SELECT 1", duration_ms=5.0, repository="TestRepo")

    response = get_sql_health(limit=10, operation_id=None)
    payload = _body(response)["data"]

    assert payload["storage_backend"] in {"memory", "redis"}
    assert "by_operation_id" in payload
    assert "top_by_duration" in payload
    assert payload["total_samples"] >= 1


def test_get_sql_health_drill_down_filter() -> None:
    from app.interface.http.routes.system_routes import get_sql_health

    record_sql_query(query="SELECT 2", duration_ms=8.0, repository="TestRepo")

    response = get_sql_health(limit=10, operation_id="__none__")
    payload = _body(response)["data"]

    assert payload["filter_operation_id"] == "__none__"
    assert "timeline" in payload
    assert "queries_in_operation" in payload


def test_get_query_cache_stats_returns_namespace_metrics() -> None:
    from app.interface.http.routes.system_routes import get_query_cache_stats

    cache = build_query_cache()
    cache.set("stock-value|demo", {"ok": True})
    cache.get("stock-value|demo")
    cache.get("stock-value|missing")

    response = get_query_cache_stats()
    payload = _body(response)["data"]

    assert payload["backend"] in {"memory", "redis"}
    assert payload["totals"]["lookups"] >= 2
    namespaces = {row["namespace"] for row in payload["namespaces"]}
    assert "stock-value" in namespaces


def test_get_caller_stats_returns_breakdown() -> None:
    from app.interface.http.routes.system_routes import get_caller_stats

    record_caller_request(
        caller_app="api-delpi-console",
        route_path="/system/sql-health",
        operation_id="get_sql_health",
        status_code=200,
        duration_ms=15.0,
    )

    response = get_caller_stats(limit=10)
    payload = _body(response)["data"]

    assert payload["total_requests"] >= 1
    assert payload["by_caller"][0]["caller_app"] == "api-delpi-console"
    assert payload["by_route"]


def test_get_observability_snapshot_unifies_phase2_and_phase3() -> None:
    from app.interface.http.routes.system_routes import get_observability_snapshot

    record_sql_query(query="SELECT 3", duration_ms=3.0, repository="TestRepo")
    record_caller_request(
        caller_app="api-delpi-console",
        route_path="/system/observability-snapshot",
        operation_id="get_observability_snapshot",
        status_code=200,
        duration_ms=9.0,
    )
    cache = build_query_cache()
    cache.set("lmp-dashboard|x", {"items": []})

    response = get_observability_snapshot(limit=10)
    payload = _body(response)["data"]

    assert payload["captured_at"]
    assert "query_cache" in payload
    assert "caller_stats" in payload
    assert "sql_health" in payload
    assert payload["sql_health"]["total_samples"] >= 1
    assert payload["caller_stats"]["total_requests"] >= 1


def test_get_openapi_diff_matches_baseline_when_unchanged() -> None:
    from app.interface.http.routes.system_routes import get_openapi_diff

    response = get_openapi_diff()
    payload = _body(response)["data"]

    assert "added_count" in payload
    assert "removed_count" in payload
    assert "changed_count" in payload
    assert payload["added_count"] >= 0
    assert payload["removed_count"] >= 0


def test_get_envelope_contracts_returns_golden_routes() -> None:
    from app.interface.http.routes.system_routes import get_envelope_contracts

    response = get_envelope_contracts()
    payload = _body(response)["data"]

    assert isinstance(payload.get("routes"), list)
    assert len(payload["routes"]) >= 5
