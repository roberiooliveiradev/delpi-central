from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.application.services.tm_sign_pending_mail_service import SignInviteMailResult
from tm_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_SEND_ACCEPTED,
)
from tm_app.middleware.auth_middleware import _is_public


def _accepted_results(*invite_ids: str) -> list[SignInviteMailResult]:
    return [
        SignInviteMailResult(
            invite_id=invite_id,
            signer_id=None,
            mail_template_key="signPending",
            mail_recipient="x@example.com",
            mail_send_status=MAIL_SEND_ACCEPTED,
            mail_delivery_status=MAIL_DELIVERY_TRACE_PENDING,
        )
        for invite_id in invite_ids
    ]


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
        {"id": "s1", "user_id": "u1", "display_name": "Ana", "invite_email": None, "status": "pending"},
        {
            "id": "s2",
            "user_id": None,
            "display_name": "Ext",
            "invite_email": "e@x.com",
            "status": "pending",
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
    mail.notify_signers.return_value = _accepted_results("inv1", "inv2")

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
    assert mail_signers[0]["invite_id"] == "inv1"
    assert mail_signers[1]["invite_email"] == "e@x.com"
    assert repo.update_invite_mail_send_result.call_count == 2


def test_send_for_signature_skips_already_signed_signers():
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
        {"id": "s1", "user_id": "u1", "display_name": "Ana", "status": "signed"},
        {"id": "s2", "user_id": "u2", "display_name": "Bruno", "status": "pending"},
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
    invites.issue.return_value = {
        "sign_url": "https://p/p/transformometro/sign/t2",
        "raw_token": "t2",
        "invite": {"id": "inv2"},
    }
    mail = MagicMock()
    mail.notify_signers.return_value = _accepted_results("inv2")

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
    assert [s["id"] for s in result["signers"]] == ["s2"]
    invites.issue.assert_called_once()
    mail.notify_signers.assert_called_once()
    assert len(mail.notify_signers.call_args.kwargs["signers"]) == 1


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
    mail.notify_signers.return_value = _accepted_results("inv2", "inv3")
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
    repo.list_participants.return_value = [
        {"user_id": None, "display_name": "Ana", "role_in_meeting": "chair", "is_external": False}
    ]
    repo.list_signers.return_value = [
        {"id": "s1", "user_id": None, "display_name": "Ana", "status": "pending"}
    ]
    repo.list_signatures.return_value = []
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
    assert ctx.get("outcome") == "ready"
    assert "body_html" in ctx["version"]
    repo.confirm_invite_mail_delivered_from_engagement.assert_called_once()
    assert repo.confirm_invite_mail_delivered_from_engagement.call_args.args[0] == "inv1"

    refused = svc.public_refuse("tok", "Ausente")
    assert refused["minute"]["id"] == "m1"
    invites.consume.assert_called_once_with("inv1")
    assert notifications.notify_minute_refused.call_count == 2


def test_public_sign_context_already_signed_includes_version_content():
    repo = MagicMock()
    invites = MagicMock()
    invites.resolve.return_value = {
        "outcome": "already_signed",
        "invite": {"id": "inv1"},
        "signer": {
            "id": "s1",
            "display_name": "Ana",
            "status": "signed",
            "user_id": None,
            "version_id": "v1",
        },
        "minute": {
            "id": "m1",
            "title": "Kickoff",
            "minute_number": "TM-9",
            "meeting_date": "2026-01-01",
            "status": "signed",
            "unit_code": "01",
        },
    }
    repo.get_version.return_value = {
        "id": "v1",
        "title": "Kickoff",
        "agenda_html": "<p>Pauta</p>",
        "body_html": "<p>Conteúdo assinado</p>",
        "decisions_html": "",
        "pending_html": "",
        "observations_html": "",
        "content_hash": "h",
    }
    repo.list_participants.return_value = []
    repo.list_signers.return_value = [
        {"id": "s1", "user_id": None, "display_name": "Ana", "status": "signed"}
    ]
    repo.list_signatures.return_value = [
        {
            "id": "sig1",
            "signer_id": "s1",
            "user_id": None,
            "display_name_confirmed": "Ana",
            "image_path": "/data/sig1.png",
        }
    ]
    svc = MeetingMinutesService(
        repo,
        notifications=MagicMock(),
        sign_invites=invites,
        sign_pending_mail=MagicMock(),
    )
    ctx = svc.public_sign_context("tok")
    assert ctx["outcome"] == "already_signed"
    assert ctx["version"]["body_html"] == "<p>Conteúdo assinado</p>"
    assert ctx["signers"][0]["status"] == "signed"
    assert ctx["signatures"][0]["id"] == "sig1"
    assert ctx["signatures"][0]["has_image"] is True
    repo.get_version.assert_called_with("m1", version_id="v1")
    repo.list_signatures.assert_called_with("m1", version_id="v1")
    repo.mark_signer_viewed.assert_not_called()
    repo.confirm_invite_mail_delivered_from_engagement.assert_called_once()
    assert repo.confirm_invite_mail_delivered_from_engagement.call_args.args[0] == "inv1"


def test_public_signature_image(tmp_path):
    image_path = tmp_path / "sig.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\npublic")
    repo = MagicMock()
    invites = MagicMock()
    invites.resolve.return_value = {
        "outcome": "already_signed",
        "invite": {"id": "inv1"},
        "signer": {"id": "s1", "status": "signed"},
        "minute": {"id": "m1"},
    }
    repo.get_signature.return_value = {"id": "sig1", "image_path": str(image_path)}
    storage = MagicMock()
    storage.read.return_value = image_path.read_bytes()
    svc = MeetingMinutesService(
        repo,
        notifications=MagicMock(),
        sign_invites=invites,
        sign_pending_mail=MagicMock(),
    )
    svc.signature_storage = storage
    assert svc.public_signature_image("tok", "sig1").startswith(b"\x89PNG")
    storage.read.assert_called_once_with(str(image_path))
