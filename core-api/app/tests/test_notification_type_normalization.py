# app/tests/test_notification_type_normalization.py

from app.application.services.notification_content_service import (
    NotificationContentService,
    NotificationContentValidationError,
)
from app.domain.notifications.notification_constants import (
    normalize_notification_type,
)


def test_normalize_notification_type_canonical_and_aliases():
    assert normalize_notification_type("info") == "info"
    assert normalize_notification_type("WARNING") == "warning"
    assert normalize_notification_type("aviso") == "info"
    assert normalize_notification_type("atenção") == "warning"
    assert normalize_notification_type("atencao") == "warning"
    assert normalize_notification_type("alerta") == "error"
    assert normalize_notification_type("sucesso") == "success"
    assert normalize_notification_type("nope") is None


def test_prepare_accepts_portuguese_severity_aliases():
    prepared = NotificationContentService().prepare(
        title="Teste",
        message="Mensagem de alerta",
        type="alerta",
        category="announcement",
        presentation="text",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata=None,
        expires_at=None,
    )
    assert prepared.type == "error"

    prepared_aviso = NotificationContentService().prepare(
        title="Teste",
        message="Mensagem de aviso",
        type="aviso",
        category="announcement",
        presentation="text",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata=None,
        expires_at=None,
    )
    assert prepared_aviso.type == "info"


def test_prepare_rejects_unknown_type():
    try:
        NotificationContentService().prepare(
            title="Teste",
            message="x",
            type="critical",
            category="announcement",
            presentation="text",
            html_content=None,
            action_type=None,
            action_label=None,
            action_target=None,
            icon=None,
            metadata=None,
            expires_at=None,
        )
        assert False, "expected validation error"
    except NotificationContentValidationError as exc:
        assert "type must be one of" in str(exc)
