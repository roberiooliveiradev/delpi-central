from types import SimpleNamespace
from unittest.mock import MagicMock

from cec_app.application.use_cases.meeting_minutes_service import MeetingMinutesService


def test_send_for_signature_notifies_each_signer():
    notifications = MagicMock()
    sign_pending_mail = MagicMock()
    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.notifications = notifications
    service.sign_pending_mail = sign_pending_mail
    service._assert = lambda *_a, **_k: None
    service._user_id = lambda _user: "actor"
    service._load_authorized = lambda *_a, **_k: {
        "id": "m1",
        "status": "draft",
        "minute_number": "2026/001",
        "title": "Reunião",
    }
    service.repo = MagicMock()
    service.repo.list_signers.return_value = [
        {"user_id": "u1"},
        {"user_id": "u2"},
    ]
    service.repo.set_status.return_value = {
        "id": "m1",
        "status": "awaiting_signatures",
        "minute_number": "2026/001",
        "title": "Reunião",
    }

    result = service.send_for_signature(SimpleNamespace(id="actor"), "m1")

    assert result["minute"]["status"] == "awaiting_signatures"
    assert notifications.notify_sign_pending.call_count == 2
    notifications.notify_sign_pending.assert_any_call(
        user_id="u1",
        minute_id="m1",
        minute_number="2026/001",
        title="Reunião",
    )
    sign_pending_mail.notify_signers.assert_called_once_with(
        signers=[{"user_id": "u1"}, {"user_id": "u2"}],
        minute_id="m1",
        minute_number="2026/001",
        title="Reunião",
    )
