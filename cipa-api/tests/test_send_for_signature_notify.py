from types import SimpleNamespace
from unittest.mock import MagicMock

from cipa_app.application.use_cases.meeting_minutes_service import MeetingMinutesService


def test_send_for_signature_issues_invites_notifies_and_mails():
    notifications = MagicMock()
    sign_pending_mail = MagicMock()
    sign_invites = MagicMock()
    sign_invites.issue.side_effect = [
        {
            "invite": {"id": "inv-1"},
            "sign_url": "https://portal/p/cipa/sign/t1",
            "raw_token": "t1",
        },
        {
            "invite": {"id": "inv-2"},
            "sign_url": "https://portal/p/cipa/sign/t2",
            "raw_token": "t2",
        },
    ]

    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.notifications = notifications
    service.sign_pending_mail = sign_pending_mail
    service.sign_invites = sign_invites
    service._assert = lambda *_a, **_k: None
    service._user_id = lambda _user: "actor"
    service._load_authorized = lambda *_a, **_k: {
        "id": "m1",
        "status": "draft",
        "minute_number": "2026/001",
        "title": "Reunião",
        "unit_code": "01",
    }
    service.repo = MagicMock()
    service.repo.list_signers.return_value = [
        {"user_id": "u1", "display_name": "Ana"},
        {"user_id": "u2", "display_name": "Bob"},
    ]
    service.repo.set_status.return_value = {
        "id": "m1",
        "status": "awaiting_signatures",
        "minute_number": "2026/001",
        "title": "Reunião",
        "unit_code": "01",
    }

    result = service.send_for_signature(SimpleNamespace(id="actor"), "m1")

    assert result["minute"]["status"] == "awaiting_signatures"
    assert sign_invites.issue.call_count == 2
    assert notifications.notify_sign_pending.call_count == 2
    sign_pending_mail.notify_signers.assert_called_once()
    mail_signers = sign_pending_mail.notify_signers.call_args.kwargs["signers"]
    assert mail_signers[0]["sign_url"] == "https://portal/p/cipa/sign/t1"


def test_resend_sign_invites_only_pending_and_keeps_minute_status():
    notifications = MagicMock()
    sign_pending_mail = MagicMock()
    sign_pending_mail.notify_signers.return_value = 1
    sign_invites = MagicMock()
    sign_invites.issue.return_value = {
        "invite": {"id": "inv-2"},
        "sign_url": "https://portal/p/cipa/sign/t2",
        "raw_token": "t2",
    }

    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.notifications = notifications
    service.sign_pending_mail = sign_pending_mail
    service.sign_invites = sign_invites
    service._assert = lambda *_a, **_k: None
    service._user_id = lambda _user: "actor"
    service._load_authorized = lambda *_a, **_k: {
        "id": "m1",
        "status": "partially_signed",
        "minute_number": "2026/010",
        "title": "Reunião",
        "unit_code": "01",
    }
    service.repo = MagicMock()
    service.repo.list_signers.return_value = [
        {"id": "s1", "user_id": "u1", "display_name": "Ana", "status": "signed"},
        {"id": "s2", "user_id": "u2", "display_name": "Bob", "status": "pending"},
    ]

    result = service.resend_sign_invites(SimpleNamespace(id="actor"), "m1")

    assert result["resent_count"] == 1
    assert result["minute"]["status"] == "partially_signed"
    assert [s["id"] for s in result["signers"]] == ["s2"]
    sign_invites.issue.assert_called_once()
    sign_pending_mail.notify_signers.assert_called_once()
    assert (
        sign_pending_mail.notify_signers.call_args.kwargs["template_key"]
        == "signPendingReminder"
    )


def test_resend_sign_invites_rejects_when_not_awaiting():
    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service._load_authorized = lambda *_a, **_k: {
        "id": "m1",
        "status": "in_review",
        "unit_code": "01",
    }

    import pytest

    with pytest.raises(ValueError, match="Reenvio só é permitido"):
        service.resend_sign_invites(SimpleNamespace(id="actor"), "m1")
