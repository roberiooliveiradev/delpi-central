from __future__ import annotations

from unittest.mock import MagicMock, patch

from cipa_app.application.services.portal_notification_service import (
    EVENT_MINUTE_REFUSED,
    EVENT_MINUTE_SIGNED,
    EVENT_SIGN_PENDING,
    CipaPortalNotificationService,
)


def test_send_builds_core_contract_with_user_ids_and_portal_route():
    service = CipaPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="svc-token",
        enabled=True,
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "{}"

    with patch(
        "cipa_app.application.services.portal_notification_service.httpx.post",
        return_value=mock_response,
    ) as post:
        ok = service.notify_sign_pending(
            user_id="user-1",
            minute_id="minute-1",
            minute_number="2026/001",
            title="Reunião ordinária",
            unit_code="01",
        )

    assert ok is True
    assert post.call_count == 1
    args, kwargs = post.call_args
    assert args[0] == "http://core-api:8000/integrations/notifications"
    body = kwargs["json"]
    assert body["userIds"] == ["user-1"]
    assert body["category"] == "cipa"
    assert body["sourceApp"] == "cipa"
    assert body["action"] == {
        "type": "portal_route",
        "label": "Assinar ata",
        "target": "/apps/cipa/filial-01/minutes/minute-1/sign",
    }
    assert body["metadata"]["event"] == EVENT_SIGN_PENDING
    assert body["metadata"]["dedupeKey"] == "cipa:sign_pending:minute-1:user-1"


def test_signed_and_refused_deep_link_to_detail():
    service = CipaPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="tok",
        enabled=True,
    )
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.text = "{}"

    with patch(
        "cipa_app.application.services.portal_notification_service.httpx.post",
        return_value=mock_response,
    ) as post:
        service.notify_minute_signed(
            user_id="u1",
            minute_id="m1",
            minute_number="2026/002",
            title="Ata",
            unit_code="02",
        )
        service.notify_minute_refused(
            user_id="u1",
            minute_id="m1",
            minute_number="2026/002",
            title="Ata",
            unit_code="02",
            actor_name="João",
            reason="Ausência",
        )

    targets = [call.kwargs["json"]["action"]["target"] for call in post.call_args_list]
    assert targets == [
        "/apps/cipa/filial-02/minutes/m1",
        "/apps/cipa/filial-02/minutes/m1",
    ]
    events = [call.kwargs["json"]["metadata"]["event"] for call in post.call_args_list]
    assert events == [EVENT_MINUTE_SIGNED, EVENT_MINUTE_REFUSED]
