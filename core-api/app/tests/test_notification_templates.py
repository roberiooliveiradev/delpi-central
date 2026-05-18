# app/tests/test_notification_templates.py

import pytest

from app.application.services.notification_content_service import (
    NotificationContentService,
    NotificationContentValidationError,
)


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
        )
