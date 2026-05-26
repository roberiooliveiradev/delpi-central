# app/tests/test_notification_recipient_vars.py

from uuid import uuid4

from app.domain.notifications.notification_recipient_vars import (
    build_recipient_template_vars,
    resolve_user_display_name,
)
from app.domain.notifications.notification_templates import NOTIFICATION_TEMPLATES
from app.domain.ports.user_repository_port import UserDTO


def _user(name: str, email: str = "usuario.teste@exemplo.com"):
    return UserDTO(
        id=uuid4(),
        email=email,
        name=name,
        active=True,
        is_superadmin=False,
        last_login_at=None,
    )


def test_resolve_user_display_name_from_full_name():
    assert resolve_user_display_name(_user("Usuaria Teste")) == "Usuaria"


def test_resolve_user_display_name_from_email_when_name_empty():
    user = _user("", email="colaborador.exemplo@exemplo.com")
    assert resolve_user_display_name(user) == "Colaborador"


def test_build_recipient_template_vars_for_welcome():
    user = _user("Admin Sistema")
    spec = NOTIFICATION_TEMPLATES["welcome_v1"]

    assert build_recipient_template_vars(user, spec) == {"userName": "Admin"}
