from app.composition.sql_telemetry_composer import reset_sql_telemetry_store_for_tests
from app.domain.services.caller_request_stats_service import reset_caller_request_stats_for_tests
from app.domain.services.console_alerts_service import reset_console_alerts_for_tests


def _body(response) -> dict:
    import json

    return json.loads(response.body.decode())


def setup_function() -> None:
    reset_console_alerts_for_tests()
    reset_caller_request_stats_for_tests()
    reset_sql_telemetry_store_for_tests()


def test_get_console_health_route() -> None:
    from app.domain.services.caller_request_stats_service import record_caller_request
    from app.interface.http.routes.system_routes import get_console_health

    record_caller_request(
        caller_app="test-app",
        route_path="/system/console-health",
        operation_id="get_console_health",
        status_code=200,
        duration_ms=12.5,
    )
    record_caller_request(
        caller_app="test-app",
        route_path="/system/console-health",
        operation_id="get_console_health",
        status_code=500,
        duration_ms=80.0,
    )

    response = get_console_health()
    payload = _body(response)["data"]

    assert payload["status"] in {"ok", "warning", "critical"}
    assert "metrics" in payload
    assert "thresholds" in payload
    assert payload["open_alerts_count"] == payload["open_alert_count"]
    assert payload["traffic"]["total_requests"] == 2
    assert payload["traffic"]["error_count"] == 1
    assert payload["traffic"]["error_rate_pct"] == 50.0
    assert payload["metrics"]["error_rate_pct"] == 50.0
    assert "pools" in payload
    assert "max_occupancy_pct" in payload["pools"]
    assert "occupancy_pct" in payload["pools"]["plugins_postgres"]
    assert "pool_occupancy_pct" in payload["metrics"]
    assert payload["slo"]["availability_pct"] == 99.0
    assert payload["slo"]["p95_ms"] == 3000.0
    assert payload["sli"]["total_requests"] == 2
    assert payload["sli"]["availability_pct"] == 50.0
    assert payload["sli"]["error_budget_remaining_pct"] == 0.0
    assert payload["sli_meta"]["window_scope"] == "in_memory_sample"


def test_post_console_alerts_smoke_route() -> None:
    from app.interface.http.routes.system_routes import post_console_alerts_smoke

    response = post_console_alerts_smoke(
        smoke_result={
            "suiteId": "qualidade-ppm",
            "passed": 2,
            "failed": 1,
            "cases": [{"caseId": "x", "ok": False, "message": "fail", "status": 422}],
        },
        notify=False,
    )
    payload = _body(response)["data"]

    assert payload["alert_count"] >= 1
    assert payload["alerts"][0]["code"] == "smoke_failure"
