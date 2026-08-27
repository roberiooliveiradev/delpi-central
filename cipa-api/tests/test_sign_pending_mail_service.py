from __future__ import annotations

from unittest.mock import MagicMock

from cipa_app.application.services.email_brand_layout_service import BLUE_900
from cipa_app.application.services.sign_pending_mail_service import (
    CipaSignPendingMailService,
    SignInviteMailResult,
    _mail_content,
)
from cipa_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_SEND_ACCEPTED,
    MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
)
from cipa_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
)


def setup_function() -> None:
    _mail_content.cache_clear()


def test_build_html_includes_public_sign_link_and_escapes_title():
    mail = MagicMock()
    directory = MagicMock()
    svc = CipaSignPendingMailService(
        mail_client=mail,
        directory=directory,
        enabled=True,
    )

    html_body = svc.build_html(
        display_name="Maria <Test>",
        minute_number="2026/001",
        title='Ata "Especial" & CIPA',
        sign_url="https://portal.example/p/cipa/sign/abc123",
    )

    assert "Maria &lt;Test&gt;" in html_body
    assert "Ata &quot;Especial&quot; &amp; CIPA" in html_body
    assert 'href="https://portal.example/p/cipa/sign/abc123"' in html_body
    assert BLUE_900 in html_body


def test_notify_signers_sends_one_mail_per_resolved_email():
    mail = MagicMock()
    mail.ensure_auth_configured.return_value = None
    directory = MagicMock()
    directory.lookup_emails_by_user_ids.return_value = {
        "u1": "a@delpi.com.br",
        "u2": "b@delpi.com.br",
    }
    svc = CipaSignPendingMailService(
        mail_client=mail,
        directory=directory,
        enabled=True,
    )

    sent = svc.notify_signers(
        signers=[
            {
                "id": "s1",
                "user_id": "u1",
                "invite_id": "inv-1",
                "display_name": "Ana",
                "sign_url": "https://portal/p/cipa/sign/t1",
            },
            {
                "id": "s2",
                "user_id": "u2",
                "invite_id": "inv-2",
                "display_name": "Bob",
                "sign_url": "https://portal/p/cipa/sign/t2",
            },
        ],
        minute_number="2026/001",
        title="Reunião",
    )

    assert len(sent) == 2
    assert all(r.mail_send_status == MAIL_SEND_ACCEPTED for r in sent)
    assert all(r.mail_delivery_status == MAIL_DELIVERY_TRACE_PENDING for r in sent)
    assert mail.send_mail_to.call_count == 2


def test_notify_signers_skips_when_graph_not_configured():
    mail = MagicMock()
    mail.ensure_auth_configured.side_effect = GraphMailError("missing config")
    directory = MagicMock()
    svc = CipaSignPendingMailService(
        mail_client=mail,
        directory=directory,
        enabled=True,
    )

    results = svc.notify_signers(
        signers=[{"user_id": "u1", "sign_url": "https://portal/p/cipa/sign/t1"}],
        minute_number="2026/001",
        title="Reunião",
    )

    assert len(results) == 1
    assert results[0].mail_send_status == MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED
    mail.send_mail_to.assert_not_called()


def test_build_subject_and_html_use_reminder_template():
    svc = CipaSignPendingMailService(
        mail_client=MagicMock(),
        directory=MagicMock(),
        enabled=True,
    )

    subject = svc.build_subject(minute_number="2026/010", template_key="signPendingReminder")
    html_body = svc.build_html(
        display_name="Ana",
        minute_number="2026/010",
        title="Reunião",
        sign_url="https://portal/p/cipa/sign/abc",
        template_key="signPendingReminder",
    )

    assert "Lembrete de assinatura" in subject
    assert "Lembrete:" in html_body
    assert "links anteriores podem ter sido substituídos" in html_body


def test_build_html_includes_hidden_invite_marker():
    svc = CipaSignPendingMailService(
        mail_client=MagicMock(),
        directory=MagicMock(),
        enabled=True,
    )

    html_body = svc.build_html(
        display_name="Ana",
        minute_number="2026/010",
        title="Reunião",
        sign_url="https://portal/p/cipa/sign/abc",
        invite_id="inv-uuid-1",
    )

    assert "<!-- X-Delpi-Invite-Id: inv-uuid-1 -->" in html_body
