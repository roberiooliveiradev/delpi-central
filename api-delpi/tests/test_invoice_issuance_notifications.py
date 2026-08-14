from __future__ import annotations

from unittest.mock import patch

from app.application.security.api_delpi_permissions import INVOICE_ISSUANCE_PROCESS
from app.application.services.invoice_issuance_portal_notification_service import (
    invoice_issuance_notifications_enabled,
    notify_request_created,
    notify_request_issued,
    notify_request_returned,
    request_portal_route,
)


def test_notifications_enabled_requires_core_api() -> None:
    with patch(
        "app.application.services.invoice_issuance_portal_notification_service.settings"
    ) as settings:
        settings.INVOICE_ISSUANCE_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        assert invoice_issuance_notifications_enabled() is True


def test_notifications_disabled_without_token() -> None:
    with patch(
        "app.application.services.invoice_issuance_portal_notification_service.settings"
    ) as settings:
        settings.INVOICE_ISSUANCE_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = ""
        assert invoice_issuance_notifications_enabled() is False


def test_request_portal_route() -> None:
    assert request_portal_route(branch_code="02", request_id="abc") == (
        "/apps/invoice-issuance/filial-02?requestId=abc"
    )
    assert request_portal_route(branch_code="01", request_id="abc") == (
        "/apps/invoice-issuance/filial-01?requestId=abc"
    )


def test_notify_created_targets_process_permission() -> None:
    with (
        patch(
            "app.application.services.invoice_issuance_portal_notification_service.settings"
        ) as settings,
        patch(
            "app.application.services.invoice_issuance_portal_notification_service._post_notification",
            return_value=True,
        ) as post,
    ):
        settings.INVOICE_ISSUANCE_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        notify_request_created(
            {
                "id": "req-1",
                "branch_code": "01",
                "party_name": "ACME",
                "created_by_name": "Ana",
                "updated_at": "2026-08-14T10:00:00+00:00",
            },
            actor_user_id="u-create",
        )
        payload = post.call_args.args[0]
        assert payload["permissionCodes"] == [INVOICE_ISSUANCE_PROCESS]
        assert payload["excludedUserIds"] == ["u-create"]
        assert payload["category"] == "invoice_issuance"
        assert payload["sourceApp"] == "invoice-issuance"


def test_notify_returned_and_issued_target_requester() -> None:
    with patch(
        "app.application.services.invoice_issuance_portal_notification_service._post_notification",
        return_value=True,
    ) as post:
        request = {
            "id": "req-1",
            "branch_code": "01",
            "party_name": "ACME",
            "created_by_user_id": "u-create",
            "return_reason": "Falta peso",
        }
        notify_request_returned(request, actor_user_id="u-process")
        notify_request_issued(request, actor_user_id="u-process")
        assert post.call_count == 2
        assert post.call_args_list[0].args[0]["userIds"] == ["u-create"]
        notify_request_returned(request, actor_user_id="u-create")
        assert post.call_count == 2
