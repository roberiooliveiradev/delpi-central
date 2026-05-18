# app/tests/test_dispatch_notifications_serialization.py

from datetime import datetime

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.services.dispatch_notifications_serialization import (
    extract_template_id,
    payload_dict_to_request,
    request_to_payload_dict,
)


def test_request_roundtrip_preserves_template_metadata():
    request = DispatchNotificationsRequest(
        title="Olá",
        message="Corpo",
        type="info",
        category="welcome",
        presentation="template",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata={"templateId": "welcome_v1", "vars": {"headline": "Hi"}},
        expires_at=datetime(2026, 6, 1, 12, 0, 0),
        broadcast=False,
        user_ids=["550e8400-e29b-41d4-a716-446655440000"],
        emails=[],
        role_ids=[],
        group_ids=[],
        source_app="portal-admin",
    )

    payload = request_to_payload_dict(request)
    restored = payload_dict_to_request(payload)

    assert restored.message == "Corpo"
    assert restored.metadata == request.metadata
    assert restored.expires_at == request.expires_at
    assert extract_template_id(restored.metadata) == "welcome_v1"
