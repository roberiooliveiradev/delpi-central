from __future__ import annotations

from unittest.mock import MagicMock

from cec_app.application.services.email_brand_layout_service import (
    BLUE_900,
    BLUE_ACCENT,
    CecEmailBrandLayoutService,
)
from cec_app.application.services.sign_pending_mail_service import (
    CecSignPendingMailService,
    _mail_content,
)
from cec_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
)


def setup_function() -> None:
    _mail_content.cache_clear()


def test_brand_bar_has_delpi_stripe_colors():
    bar = CecEmailBrandLayoutService.brand_bar_html()
    assert BLUE_900 in bar
    assert BLUE_ACCENT in bar
    assert bar.count("<td width=\"25%\"") == 4


def test_build_html_includes_portal_link_brand_bars_and_escapes_title():
    mail = MagicMock()
    directory = MagicMock()
    svc = CecSignPendingMailService(
        mail_client=mail,
        directory=directory,
        enabled=True,
        public_base_url="https://portal.example",
        logo_attachment={},  # força layout sem cid
    )

    html_body = svc.build_html(
        display_name="Maria <Test>",
        minute_number="2026/001",
        title='Ata "Especial" & Conduta',
        minute_id="11111111-1111-1111-1111-111111111111",
        include_logo=False,
    )

    assert "Maria &lt;Test&gt;" in html_body
    assert "Ata &quot;Especial&quot; &amp; Conduta" in html_body
    assert (
        'href="https://portal.example/apps/comite-etica-conduta/atas/'
        '11111111-1111-1111-1111-111111111111/sign"'
    ) in html_body
    assert "Comitê de Ética e Conduta" in html_body
    assert "Integridade, respeito e responsabilidade" in html_body
    assert html_body.count(BLUE_900) >= 2  # título + CTA + rodapé
    assert BLUE_ACCENT in html_body
    assert "www.delpi.com.br" in html_body
    assert 'color:#FFFFFF' in html_body or "color:#FFFFFF !important" in html_body
    assert "Minha DELPI — Comitê de Ética e Conduta" in html_body
    assert "Assinatura pendente" not in html_body  # subject only


def test_notify_signers_sends_one_mail_per_resolved_email_with_logo():
    mail = MagicMock()
    mail.ensure_auth_configured.return_value = None
    directory = MagicMock()
    directory.lookup_emails_by_user_ids.return_value = {
        "u1": "a@delpi.com.br",
        "u2": "b@delpi.com.br",
    }
    logo = {
        "name": "logo-comite-etica.png",
        "content_type": "image/png",
        "content_base64": "YWJj",
        "is_inline": True,
        "content_id": "cec-logo",
    }
    svc = CecSignPendingMailService(
        mail_client=mail,
        directory=directory,
        enabled=True,
        public_base_url="http://localhost",
        logo_attachment=logo,
    )

    sent = svc.notify_signers(
        signers=[
            {"user_id": "u1", "display_name": "Ana"},
            {"user_id": "u2", "display_name": "Bruno"},
            {"user_id": "u3", "display_name": "Sem email"},
        ],
        minute_id="m1",
        minute_number="2026/002",
        title="Reunião",
    )

    assert sent == 2
    assert mail.send_mail_to.call_count == 2
    first = mail.send_mail_to.call_args_list[0].kwargs
    assert first["to_addresses"] == ["a@delpi.com.br"]
    assert "2026/002" in first["subject"]
    assert first["attachments"] == [logo]
    assert "cid:cec-logo" in first["html_body"]


def test_notify_signers_skips_when_graph_not_configured():
    mail = MagicMock()
    mail.ensure_auth_configured.side_effect = GraphMailError("missing")
    directory = MagicMock()
    svc = CecSignPendingMailService(
        mail_client=mail,
        directory=directory,
        enabled=True,
        public_base_url="http://localhost",
        logo_attachment={},
    )

    sent = svc.notify_signers(
        signers=[{"user_id": "u1", "display_name": "Ana"}],
        minute_id="m1",
        minute_number="1",
        title="T",
    )

    assert sent == 0
    directory.lookup_emails_by_user_ids.assert_not_called()
    mail.send_mail_to.assert_not_called()


def test_notify_signers_disabled():
    mail = MagicMock()
    directory = MagicMock()
    svc = CecSignPendingMailService(
        mail_client=mail,
        directory=directory,
        enabled=False,
        public_base_url="http://localhost",
    )

    assert (
        svc.notify_signers(
            signers=[{"user_id": "u1"}],
            minute_id="m1",
            minute_number="1",
            title="T",
        )
        == 0
    )
    mail.ensure_auth_configured.assert_not_called()
