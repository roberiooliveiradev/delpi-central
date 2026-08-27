from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cipa_app.application.use_cases.meeting_minutes_service import MeetingMinutesService
from cipa_app.middleware.auth_middleware import _is_public


def test_is_public_sign_invite_paths():
    assert _is_public("/public/meeting-minutes/sign-invites/abc") is True
    assert _is_public("/public/sipat/abc") is True
    assert _is_public("/health") is True
    assert _is_public("/minutes") is False


def _service_with_mocks(*, repo: MagicMock, invites: MagicMock) -> MeetingMinutesService:
    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.repo = repo
    service.sign_invites = invites
    service.notifications = MagicMock()
    service.sign_pending_mail = MagicMock()
    service.signature_storage = MagicMock()
    service.mail_engagement = MagicMock()
    return service


def test_public_sign_context_and_refuse():
    repo = MagicMock()
    invites = MagicMock()
    invites.resolve.return_value = {
        "invite": {"id": "inv1"},
        "signer": {
            "id": "s1",
            "display_name": "Ana",
            "status": "pending",
            "user_id": "u1",
        },
        "minute": {
            "id": "m1",
            "title": "Reunião",
            "minute_number": "2026/001",
            "meeting_date": "2026-01-01",
            "status": "awaiting_signatures",
            "unit_code": "01",
            "responsible_user_id": "r1",
        },
        "outcome": "ready",
    }
    repo.mark_signer_viewed.return_value = {
        "id": "s1",
        "display_name": "Ana",
        "status": "viewed",
    }
    repo.get_signer.return_value = {
        "id": "s1",
        "display_name": "Ana",
        "status": "viewed",
        "user_id": "u1",
    }
    repo.list_participants.return_value = []
    repo.list_signers.return_value = [
        {"id": "s1", "user_id": "u1", "display_name": "Ana", "status": "pending"}
    ]
    repo.list_signatures.return_value = []
    repo.get_version.return_value = {
        "id": "v1",
        "title": "Reunião",
        "agenda_html": "",
        "body_html": "<p>corpo</p>",
        "decisions_html": "",
        "pending_html": "",
        "observations_html": "",
        "content_hash": "h",
    }
    repo.set_status.return_value = {
        "id": "m1",
        "minute_number": "2026/001",
        "title": "Reunião",
        "responsible_user_id": "r1",
        "unit_code": "01",
        "status": "in_review",
    }

    service = _service_with_mocks(repo=repo, invites=invites)
    ctx = service.public_sign_context("token-abc")
    assert ctx["outcome"] == "ready"
    assert ctx["minute"]["id"] == "m1"
    assert ctx["version"]["body_html"] == "<p>corpo</p>"
    repo.mark_signer_viewed.assert_called_once_with("s1")
    service.mail_engagement.confirm_delivered_if_pending.assert_called_once_with("inv1")

    result = service.public_refuse("token-abc", "Não concordo")
    assert result["minute"]["status"] == "in_review"
    repo.refuse_signature.assert_called_once()
    invites.consume.assert_called_once_with("inv1")
    service.notifications.notify_minute_refused.assert_called_once()


def test_public_sign_rejects_already_signed():
    invites = MagicMock()
    invites.resolve.return_value = {
        "invite": {"id": "inv1"},
        "signer": {"id": "s1", "user_id": "u1"},
        "minute": {"id": "m1", "unit_code": "01"},
        "outcome": "already_signed",
    }
    service = _service_with_mocks(repo=MagicMock(), invites=invites)

    with pytest.raises(ValueError, match="já foi registrada"):
        service.public_sign(
            "token",
            png_bytes=b"png",
            display_name_confirmed="Ana",
            terms_accepted=True,
            client_ip=None,
            user_agent=None,
            session_id=None,
            idempotency_key=None,
        )
    service.mail_engagement.confirm_delivered_if_pending.assert_not_called()


def test_public_sign_context_confirms_mail_on_already_signed():
    repo = MagicMock()
    invites = MagicMock()
    invites.resolve.return_value = {
        "invite": {"id": "inv1"},
        "signer": {
            "id": "s1",
            "display_name": "Ana",
            "status": "signed",
            "user_id": "u1",
            "version_id": "v1",
        },
        "minute": {
            "id": "m1",
            "title": "Reunião",
            "minute_number": "2026/001",
            "meeting_date": "2026-01-01",
            "status": "signed",
            "unit_code": "01",
            "responsible_user_id": "r1",
        },
        "outcome": "already_signed",
    }
    repo.get_signer.return_value = invites.resolve.return_value["signer"]
    repo.list_participants.return_value = []
    repo.list_signers.return_value = []
    repo.list_signatures.return_value = []
    repo.get_version.return_value = {
        "id": "v1",
        "title": "Reunião",
        "agenda_html": "",
        "body_html": "<p>corpo</p>",
        "decisions_html": "",
        "pending_html": "",
        "observations_html": "",
        "content_hash": "h",
    }

    service = _service_with_mocks(repo=repo, invites=invites)
    ctx = service.public_sign_context("token-abc")
    assert ctx["outcome"] == "already_signed"
    service.mail_engagement.confirm_delivered_if_pending.assert_called_once_with("inv1")
    repo.mark_signer_viewed.assert_not_called()
