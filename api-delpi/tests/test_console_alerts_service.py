from unittest.mock import patch

from app.domain.services.caller_request_stats_service import (
    record_caller_request,
    reset_caller_request_stats_for_tests,
)
from app.domain.services.console_alerts_service import (
    evaluate_console_alerts,
    process_console_alerts,
    reset_console_alerts_for_tests,
)
from app.domain.services.sql_query_telemetry_service import record_sql_query
from app.composition.sql_telemetry_composer import reset_sql_telemetry_store_for_tests


def setup_function() -> None:
    reset_console_alerts_for_tests()
    reset_caller_request_stats_for_tests()
    reset_sql_telemetry_store_for_tests()


def test_evaluate_smoke_failure_alert() -> None:
    alerts = evaluate_console_alerts(
        smoke_result={
            "suiteId": "essencial",
            "passed": 2,
            "failed": 1,
            "cases": [
                {"caseId": "x", "label": "Falha", "ok": False, "message": "HTTP 500", "status": 500},
            ],
        }
    )

    assert len(alerts) == 1
    assert alerts[0].code == "smoke_failure"
    assert alerts[0].severity == "critical"


def test_evaluate_p95_alert() -> None:
    for ms in [100, 200, 500, 1000, 4000]:
        record_caller_request(
            caller_app="api-delpi-console",
            route_path="/engineering/lmps/dashboard/summary",
            operation_id="get_lmps_dashboard_summary",
            status_code=200,
            duration_ms=ms,
        )

    alerts = evaluate_console_alerts()
    codes = {alert.code for alert in alerts}
    assert "p95_latency" in codes


class _SyncThread:
    def __init__(self, target=None, args=(), **kwargs):
        self._target = target
        self._args = args

    def start(self):
        if self._target:
            self._target(*self._args)


def test_process_console_alerts_stores_history() -> None:
    with patch(
        "app.domain.services.console_alerts_service._send_webhook_sync",
    ) as webhook_mock:
        with patch(
            "app.domain.services.console_alerts_service.send_console_alert_portal_notifications",
        ) as portal_mock:
            with patch(
                "app.domain.services.console_alerts_service.threading.Thread",
                _SyncThread,
            ):
                with patch("app.domain.services.console_alerts_service.settings") as settings:
                    settings.CONSOLE_ALERT_WEBHOOK_URL = "https://example.test/hook"
                    settings.CONSOLE_ALERT_WEBHOOK_ENABLED = True
                    settings.CONSOLE_ALERT_PORTAL_ENABLED = False
                    settings.CONSOLE_ALERT_P95_THRESHOLD_MS = "3000"
                    settings.CONSOLE_ALERT_SLOW_SQL_THRESHOLD_MS = "2500"

                    result = process_console_alerts(
                        smoke_result={"suiteId": "essencial", "passed": 0, "failed": 1, "cases": []},
                        notify=True,
                    )

    assert result["alert_count"] >= 1
    assert result["stored"]
    webhook_mock.assert_called_once()
    portal_mock.assert_not_called()


def test_slow_sql_alert() -> None:
    record_sql_query(query="SELECT slow", duration_ms=5000, repository="SlowRepo")

    alerts = evaluate_console_alerts()
    assert any(alert.code == "slow_sql" for alert in alerts)
