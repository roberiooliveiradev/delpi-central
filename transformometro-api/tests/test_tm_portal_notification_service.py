from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.tm_portal_notification_service import (
    EVENT_MINUTE_REFUSED,
    EVENT_MINUTE_SIGNED,
    EVENT_SIGN_PENDING,
    TmPortalNotificationService,
)


def test_send_builds_core_contract_with_user_ids_and_portal_route():
    service = TmPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="svc-token",
        enabled=True,
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "{}"

    with patch(
        "tm_app.application.services.tm_portal_notification_service.httpx.post",
        return_value=mock_response,
    ) as post:
        ok = service.notify_sign_pending(
            user_id="user-1",
            minute_id="minute-1",
            minute_number="TM-2026/001",
            title="Reunião Transforma+",
        )

    assert ok is True
    assert post.call_count == 1
    args, kwargs = post.call_args
    assert args[0] == "http://core-api:8000/integrations/notifications"
    assert kwargs["headers"]["Authorization"] == "Bearer svc-token"
    body = kwargs["json"]
    assert body["userIds"] == ["user-1"]
    assert body["category"] == "transformometro"
    assert body["sourceApp"] == "transformometro"
    assert body["action"] == {
        "type": "portal_route",
        "label": "Assinar ata",
        "target": "/apps/transformometro/atas/minute-1/sign",
    }
    assert body["metadata"]["event"] == EVENT_SIGN_PENDING
    assert body["metadata"]["dedupeKey"] == "tm:sign_pending:minute-1:user-1"


def test_signed_and_refused_deep_link_to_detail():
    service = TmPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="tok",
        enabled=True,
    )
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.text = "{}"

    with patch(
        "tm_app.application.services.tm_portal_notification_service.httpx.post",
        return_value=mock_response,
    ) as post:
        service.notify_minute_signed(
            user_id="u1",
            minute_id="m1",
            minute_number="TM-2026/002",
            title="Ata",
        )
        service.notify_minute_refused(
            user_id="u1",
            minute_id="m1",
            minute_number="TM-2026/002",
            title="Ata",
            actor_name="João",
            reason="Ausência",
        )

    targets = [call.kwargs["json"]["action"]["target"] for call in post.call_args_list]
    assert targets == [
        "/apps/transformometro/atas/m1",
        "/apps/transformometro/atas/m1",
    ]
    events = [call.kwargs["json"]["metadata"]["event"] for call in post.call_args_list]
    assert events == [EVENT_MINUTE_SIGNED, EVENT_MINUTE_REFUSED]


def test_disabled_skips_http():
    service = TmPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="tok",
        enabled=False,
    )
    with patch(
        "tm_app.application.services.tm_portal_notification_service.httpx.post"
    ) as post:
        assert (
            service.notify_sign_pending(
                user_id="u1",
                minute_id="m1",
                minute_number="TM-2026/001",
                title="t",
            )
            is False
        )
    post.assert_not_called()
