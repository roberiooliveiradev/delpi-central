from unittest.mock import MagicMock

from tm_app.application.services.sign_invite_mail_presentation_service import (
    build_last_invite_mail,
    enrich_signers_with_last_invite_mail,
)


def test_build_last_invite_mail_includes_labels():
    payload = build_last_invite_mail(
        {
            "id": "inv-1",
            "mail_template_key": "signPending",
            "mail_recipient": "a@delpi.com.br",
            "mail_send_status": "accepted",
            "mail_delivery_status": "delivered",
            "mail_sent_at": "2026-08-27T12:00:00+00:00",
            "mail_delivered_at": "2026-08-27T12:30:00+00:00",
            "mail_last_error": None,
        }
    )
    assert payload is not None
    assert payload["delivery_status_label"] == "Entregue"


def test_enrich_signers_with_last_invite_mail():
    repo = MagicMock()
    repo.get_latest_invite_mail_by_signer_ids.return_value = {
        "s2": {
            "id": "inv-2",
            "mail_template_key": "signPendingReminder",
            "mail_recipient": "ext@partner.com",
            "mail_send_status": "accepted",
            "mail_delivery_status": "trace_pending",
            "mail_sent_at": "2026-08-27T12:00:00+00:00",
            "mail_delivered_at": None,
            "mail_last_error": None,
        }
    }
    signers = enrich_signers_with_last_invite_mail(
        repo=repo,
        minute_id="m1",
        signers=[{"id": "s1"}, {"id": "s2"}],
    )
    assert signers[0]["last_invite_mail"] is None
    assert signers[1]["last_invite_mail"]["template_key"] == "signPendingReminder"
