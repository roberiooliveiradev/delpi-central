# app/tests/test_notification_content_service.py

import pytest

from app.application.services.notification_content_service import (
    NotificationContentService,
    NotificationContentValidationError,
)


def test_prepare_html_and_portal_action():
    service = NotificationContentService()

    prepared = service.prepare(
        title="Evento",
        message="Resumo em texto",
        type="info",
        category="company_event",
        presentation="html",
        html_content="<p>Detalhes do <strong>evento</strong></p><script>alert(1)</script>",
        action_type="portal_route",
        action_label="Ver agenda",
        action_target="/admin",
        icon=None,
        metadata={"eventName": "Confraternização"},
        expires_at=None,
    )

    assert prepared.presentation == "html"
    assert "<script>" not in (prepared.html_content or "")
    assert prepared.action_type == "portal_route"
    assert prepared.category == "company_event"


def test_reject_external_url_without_https():
    service = NotificationContentService()

    with pytest.raises(NotificationContentValidationError):
        service.prepare(
            title=None,
            message="Link",
            type="info",
            category="system",
            presentation="text",
            html_content=None,
            action_type="external_url",
            action_label="Site",
            action_target="http://insecure.example.com",
            icon=None,
            metadata=None,
            expires_at=None,
        )
