from unittest.mock import patch

from app.application.services.console_portal_notification_service import (
    portal_notifications_enabled,
    send_console_alert_portal_notifications,
)


def test_portal_notifications_enabled_requires_core_api() -> None:
    with patch("app.application.services.console_portal_notification_service.settings") as settings:
        settings.CONSOLE_ALERT_PORTAL_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        assert portal_notifications_enabled() is True


def test_send_console_alert_portal_notifications_posts_to_core_api() -> None:
    with patch("app.application.services.console_portal_notification_service.settings") as settings:
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"

        with patch("httpx.Client") as client_cls:
            client = client_cls.return_value.__enter__.return_value
            client.post.return_value.status_code = 201

            sent = send_console_alert_portal_notifications(
                [
                    {
                        "code": "slow_sql",
                        "severity": "warning",
                        "message": "Query lenta detectada (3000 ms).",
                        "details": {
                            "preview": "SELECT 1",
                            "operation_id": "get_stock_value",
                        },
                    }
                ]
            )

    assert sent is True
    client.post.assert_called_once()
    payload = client.post.call_args.kwargs["json"]
    assert payload["sourceApp"] == "api-delpi-console"
    assert payload["category"] == "api_console"
    assert payload["broadcast"] is True
    assert payload["action"]["target"] == "/apps/api-delpi-console/alertas"
