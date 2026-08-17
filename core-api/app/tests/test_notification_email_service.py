# app/tests/test_notification_email_service.py

from unittest.mock import MagicMock, patch

from app.application.services.notification_email_service import (
    NotificationEmailService,
    build_notification_email_html,
)
from app.domain.notifications.notification_preference_policy import is_email_channel_enabled


def test_is_email_channel_enabled_important_or_opt_in():
    assert is_email_channel_enabled(
        "commercial",
        muted_categories=[],
        important_categories=["commercial"],
        email_categories=[],
    )
    assert is_email_channel_enabled(
        "commercial",
        muted_categories=[],
        important_categories=[],
        email_categories=["commercial"],
    )
    assert not is_email_channel_enabled(
        "commercial",
        muted_categories=["commercial"],
        important_categories=["commercial"],
        email_categories=["commercial"],
    )


def test_build_notification_email_html_subject_and_body():
    subject, body = build_notification_email_html(
        title="Pedido urgente",
        message="Há 3 notas para faturar",
        notification_type="error",
        application_name="Portal Comercial",
        portal_base_url="https://portal.example",
    )
    assert subject.startswith("[Alerta] Pedido urgente")
    assert "Há 3 notas para faturar" in body
    assert "https://portal.example/notifications" in body
    assert "Portal Comercial" in body


@patch.dict("os.environ", {"CORE_NOTIFICATION_MAIL_ENABLED": "true"}, clear=False)
def test_send_if_enabled_calls_mail_client():
    mail = MagicMock()
    ok = NotificationEmailService(mail_client=mail).send_if_enabled(
        to_email="user@delpi.com.br",
        title="Título",
        message="Corpo",
        notification_type="info",
        application_name="Minha DELPI",
    )
    assert ok is True
    mail.send_mail_to.assert_called_once()
    kwargs = mail.send_mail_to.call_args.kwargs
    assert kwargs["to_addresses"] == ["user@delpi.com.br"]
    assert "[Minha DELPI]" in kwargs["subject"]


@patch.dict("os.environ", {"CORE_NOTIFICATION_MAIL_ENABLED": "false"}, clear=False)
def test_send_skipped_when_disabled():
    mail = MagicMock()
    ok = NotificationEmailService(mail_client=mail).send_if_enabled(
        to_email="user@delpi.com.br",
        title="Título",
        message="Corpo",
        notification_type="info",
    )
    assert ok is False
    mail.send_mail_to.assert_not_called()
