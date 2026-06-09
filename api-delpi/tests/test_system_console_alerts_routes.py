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
    from app.interface.http.routes.system_routes import get_console_health

    response = get_console_health()
    payload = _body(response)["data"]

    assert payload["status"] in {"ok", "warning", "critical"}
    assert "metrics" in payload
    assert "thresholds" in payload


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
