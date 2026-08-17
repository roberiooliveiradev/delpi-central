from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.middleware.auth_middleware import _is_public


def test_is_public_paths():
    assert _is_public("/public/atas/sign-invites/abc") is True
    assert _is_public("/public/meeting-minutes/sign-invites/abc") is True
    assert _is_public("/health") is True
    assert _is_public("/transformometro/atas") is False
    assert _is_public("/transformometro/meeting-minutes") is False


def test_send_for_signature_issues_invites_notifies_and_mails():
    repo = MagicMock()
    repo.get_minute.return_value = {
        "id": "m1",
        "unit_code": "01",
        "status": "in_review",
        "minute_number": "TM-1",
        "title": "Ata",
        "current_version_id": "v1",
    }
    repo.list_signers.return_value = [
        {"id": "s1", "user_id": "u1", "display_name": "Ana", "invite_email": None},
        {
            "id": "s2",
            "user_id": None,
            "display_name": "Ext",
            "invite_email": "e@x.com",
        },
    ]
    repo.set_status.return_value = {
        "id": "m1",
        "unit_code": "01",
        "status": "awaiting_signatures",
        "minute_number": "TM-1",
        "title": "Ata",
    }
    notifications = MagicMock()
    invites = MagicMock()
    invites.issue.side_effect = [
        {
            "sign_url": "https://p/p/transformometro/sign/t1",
            "raw_token": "t1",
            "invite": {"id": "inv1"},
        },
        {
            "sign_url": "https://p/p/transformometro/sign/t2",
            "raw_token": "t2",
            "invite": {"id": "inv2"},
        },
    ]
    mail = MagicMock()
    mail.notify_signers.return_value = 2

    user = MagicMock(id="mgr", is_superadmin=True, permissions=[])
    svc = MeetingMinutesService(
        repo,
        notifications=notifications,
        sign_invites=invites,
        sign_pending_mail=mail,
    )
    svc.scope_service = MagicMock()

    result = svc.send_for_signature(user, "m1")
    assert result["minute"]["status"] == "awaiting_signatures"
    assert invites.issue.call_count == 2
    assert notifications.notify_sign_pending.call_count == 1
    assert notifications.notify_sign_pending.call_args.kwargs["dedupe_key"] == (
        "tm:sign_pending:m1:u1:inv1"
    )
    mail.notify_signers.assert_called_once()
    assert mail.notify_signers.call_args.kwargs["template_key"] == "signPending"
    mail_signers = mail.notify_signers.call_args.kwargs["signers"]
    assert mail_signers[0]["sign_url"].endswith("/t1")
    assert mail_signers[1]["invite_email"] == "e@x.com"


def test_resend_sign_invites_only_pending_and_keeps_minute_status():
    repo = MagicMock()
    repo.get_minute.return_value = {
        "id": "m1",
        "unit_code": "01",
        "status": "partially_signed",
        "minute_number": "TM-1",
        "title": "Ata",
        "current_version_id": "v1",
    }
    repo.list_signers.return_value = [
        {"id": "s1", "user_id": "u1", "display_name": "Ana", "status": "signed"},
        {
            "id": "s2",
            "user_id": "u2",
            "display_name": "Bruno",
            "status": "pending",
            "invite_email": None,
        },
        {
            "id": "s3",
            "user_id": None,
            "display_name": "Ext",
            "status": "viewed",
            "invite_email": "e@x.com",
        },
    ]
    notifications = MagicMock()
    invites = MagicMock()
    invites.issue.side_effect = [
        {
            "sign_url": "https://p/p/transformometro/sign/t2",
            "raw_token": "t2",
            "invite": {"id": "inv2"},
        },
        {
            "sign_url": "https://p/p/transformometro/sign/t3",
            "raw_token": "t3",
            "invite": {"id": "inv3"},
        },
    ]
    mail = MagicMock()
    mail.notify_signers.return_value = 2
    user = MagicMock(id="mgr", is_superadmin=True, permissions=[])
    svc = MeetingMinutesService(
        repo,
        notifications=notifications,
        sign_invites=invites,
        sign_pending_mail=mail,
    )
    svc.scope_service = MagicMock()

    result = svc.resend_sign_invites(user, "m1")
    assert result["resent_count"] == 2
    assert result["minute"]["status"] == "partially_signed"
    assert [s["id"] for s in result["signers"]] == ["s2", "s3"]
    assert invites.issue.call_count == 2
    repo.set_status.assert_not_called()
    assert mail.notify_signers.call_args.kwargs["template_key"] == "signPendingReminder"
    assert notifications.notify_sign_pending.call_count == 1


def test_resend_sign_invites_rejects_when_not_awaiting():
    repo = MagicMock()
    repo.get_minute.return_value = {
        "id": "m1",
        "unit_code": "01",
        "status": "in_review",
        "minute_number": "TM-1",
        "title": "Ata",
        "current_version_id": "v1",
    }
    user = MagicMock(id="mgr", is_superadmin=True, permissions=[])
    svc = MeetingMinutesService(repo, notifications=MagicMock())
    svc.scope_service = MagicMock()
    import pytest

    with pytest.raises(ValueError, match="Reenvio só é permitido"):
        svc.resend_sign_invites(user, "m1")


def test_public_sign_context_and_refuse():
    repo = MagicMock()
    invites = MagicMock()
    invites.resolve.return_value = {
        "invite": {"id": "inv1"},
        "signer": {"id": "s1", "display_name": "Ana", "status": "pending", "user_id": None},
        "minute": {
            "id": "m1",
            "title": "T",
            "minute_number": "1",
            "meeting_date": "2026-01-01",
            "status": "awaiting_signatures",
            "unit_code": "01",
            "created_by_user_id": "c1",
            "responsible_user_id": "r1",
        },
    }
    repo.mark_signer_viewed.return_value = {
        "id": "s1",
        "display_name": "Ana",
        "status": "viewed",
    }
    repo.get_version.return_value = {
        "id": "v1",
        "title": "T",
        "agenda_html": "",
        "body_html": "<p>x</p>",
        "decisions_html": "",
        "pending_html": "",
        "observations_html": "",
        "content_hash": "h",
    }
    repo.set_status.return_value = {
        "id": "m1",
        "minute_number": "1",
        "title": "T",
        "created_by_user_id": "c1",
        "responsible_user_id": "r1",
    }
    notifications = MagicMock()
    svc = MeetingMinutesService(
        repo,
        notifications=notifications,
        sign_invites=invites,
        sign_pending_mail=MagicMock(),
    )

    ctx = svc.public_sign_context("tok")
    assert ctx["signer"]["display_name"] == "Ana"
    assert "body_html" in ctx["version"]

    refused = svc.public_refuse("tok", "Ausente")
    assert refused["minute"]["id"] == "m1"
    invites.consume.assert_called_once_with("inv1")
    assert notifications.notify_minute_refused.call_count == 2
