# app/tests/test_notification_templates.py

import pytest

from app.application.services.notification_content_service import (
    NotificationContentService,
    NotificationContentValidationError,
)
from app.domain.notifications.notification_templates import NOTIFICATION_TEMPLATES


def test_prepare_welcome_template():
    service = NotificationContentService()

    prepared = service.prepare(
        title=None,
        message="",
        type="info",
        category="welcome",
        presentation="template",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata={"templateId": "welcome_v1", "vars": {"userName": "Maria"}},
        expires_at=None,
        template_spec=NOTIFICATION_TEMPLATES["welcome_v1"],
    )

    assert prepared.presentation == "template"
    assert "Maria" in prepared.message
    assert prepared.metadata["templateId"] == "welcome_v1"


def test_prepare_welcome_template_auto_recipient_name():
    service = NotificationContentService()

    prepared = service.prepare(
        title=None,
        message="",
        type="info",
        category="welcome",
        presentation="template",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata={"templateId": "welcome_v1", "vars": {}},
        expires_at=None,
        recipient_context={"userName": "Maria"},
        template_spec=NOTIFICATION_TEMPLATES["welcome_v1"],
    )

    assert "Maria" in prepared.message
    assert prepared.metadata["vars"]["userName"] == "Maria"


def test_prepare_template_missing_recipient_var():
    service = NotificationContentService()

    with pytest.raises(NotificationContentValidationError):
        service.prepare(
            title=None,
            message="",
            type="info",
            category="birthday",
            presentation="template",
            html_content=None,
            action_type=None,
            action_label=None,
            action_target=None,
            icon=None,
            metadata={"templateId": "birthday_v1", "vars": {}},
            expires_at=None,
            recipient_context=None,
            template_spec=NOTIFICATION_TEMPLATES["birthday_v1"],
        )


def test_prepare_company_event_requires_event_name():
    service = NotificationContentService()

    with pytest.raises(NotificationContentValidationError):
        service.prepare(
            title=None,
            message="",
            type="info",
            category="company_event",
            presentation="template",
            html_content=None,
            action_type=None,
            action_label=None,
            action_target=None,
            icon=None,
            metadata={"templateId": "company_event_v1", "vars": {}},
            expires_at=None,
            template_spec=NOTIFICATION_TEMPLATES["company_event_v1"],
        )


def test_prepare_html_with_recipient_variables():
    service = NotificationContentService()

    prepared = service.prepare(
        title="Olá, {userName}",
        message="Resumo para {userEmail}",
        type="info",
        category="announcement",
        presentation="html",
        html_content="<p>Caro(a) <strong>{userFullName}</strong>, bem-vindo!</p>",
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata=None,
        expires_at=None,
        recipient_context={
            "userName": "Ana",
            "userFullName": "Ana Paula",
            "userEmail": "ana@empresa.com",
        },
    )

    assert "Ana Paula" in prepared.html_content
    assert "Ana" in (prepared.title or "")
