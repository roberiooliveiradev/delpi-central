from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.tm_sign_pending_mail_service import (
    TmSignPendingMailService,
    _mail_content,
)
from tm_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_SEND_ACCEPTED,
    MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
    MAIL_SEND_SKIPPED_NO_EMAIL,
)
from tm_app.infrastructure.gateways.core_directory_service import TmCoreDirectoryService
from tm_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
)


def setup_function() -> None:
    _mail_content.cache_clear()


def test_build_html_includes_magic_link_and_escapes():
    mail = MagicMock()
    directory = MagicMock()
    svc = TmSignPendingMailService(mail_client=mail, directory=directory, enabled=True)
    html_body = svc.build_html(
        display_name="Maria <Test>",
        minute_number="TM-001",
        title='Ata "Especial" & Mais',
        sign_url="https://portal.example/p/transformometro/sign/tok-abc",
    )
    assert "Maria &lt;Test&gt;" in html_body
    assert "Ata &quot;Especial&quot; &amp; Mais" in html_body
    assert 'href="https://portal.example/p/transformometro/sign/tok-abc"' in html_body
    assert "Transformômetro" in html_body


def test_notify_signers_uses_directory_and_invite_email():
    mail = MagicMock()
    mail.ensure_auth_configured.return_value = None
    directory = MagicMock()
    directory.lookup_emails_by_user_ids.return_value = {"u1": "a@delpi.com.br"}
    svc = TmSignPendingMailService(mail_client=mail, directory=directory, enabled=True)

    sent = svc.notify_signers(
        signers=[
            {
                "id": "s1",
                "user_id": "u1",
                "invite_id": "inv-1",
                "display_name": "Ana",
                "sign_url": "https://p/p/transformometro/sign/t1",
            },
            {
                "id": "s2",
                "user_id": None,
                "invite_id": "inv-2",
                "invite_email": "ext@partner.com",
                "display_name": "Externo",
                "sign_url": "https://p/p/transformometro/sign/t2",
            },
            {
                "id": "s3",
                "user_id": "u3",
                "invite_id": "inv-3",
                "display_name": "Sem email",
                "sign_url": "https://p/p/transformometro/sign/t3",
            },
        ],
        minute_number="TM-002",
        title="Reunião",
    )

    assert len(sent) == 3
    assert sum(1 for r in sent if r.mail_send_status == MAIL_SEND_ACCEPTED) == 2
    assert sent[2].mail_send_status == MAIL_SEND_SKIPPED_NO_EMAIL
    assert mail.send_mail_to.call_count == 2
    emails = [c.kwargs["to_addresses"][0] for c in mail.send_mail_to.call_args_list]
    assert emails == ["a@delpi.com.br", "ext@partner.com"]
    assert "/p/transformometro/sign/" in mail.send_mail_to.call_args_list[0].kwargs["html_body"]


def test_notify_signers_skips_when_graph_not_configured():
    mail = MagicMock()
    mail.ensure_auth_configured.side_effect = GraphMailError("missing")
    directory = MagicMock()
    svc = TmSignPendingMailService(mail_client=mail, directory=directory, enabled=True)
    results = svc.notify_signers(
        signers=[{"user_id": "u1", "sign_url": "x"}],
        minute_number="1",
        title="T",
    )
    assert len(results) == 1
    assert results[0].mail_send_status == MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED
    directory.lookup_emails_by_user_ids.assert_not_called()


def test_directory_lookup_maps_items():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {"id": "u1", "email": "a@delpi.com.br"},
            {"id": "u2", "email": "bad"},
        ]
    }
    with patch(
        "tm_app.infrastructure.gateways.core_directory_service.httpx.post",
        return_value=mock_response,
    ):
        svc = TmCoreDirectoryService(
            core_api_url="http://core-api:8000",
            service_token="tok",
        )
        assert svc.lookup_emails_by_user_ids(["u1", "u2"]) == {"u1": "a@delpi.com.br"}
