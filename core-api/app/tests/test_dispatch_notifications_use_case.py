# app/tests/test_dispatch_notifications_use_case.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsUseCase,
)
from app.domain.ports.user_repository_port import UserDTO


@pytest.fixture
def uow():
    unit = MagicMock()
    unit.notifications.create.return_value = uuid4()
    unit.notification_preferences.filter_user_ids_accepting_category.side_effect = (
        lambda user_ids, _category: user_ids
    )
    return unit


def _user(user_id=None, email="a@delpi.com", active=True):
    return UserDTO(
        id=user_id or uuid4(),
        email=email,
        name="User",
        active=active,
        is_superadmin=False,
        last_login_at=None,
    )


def test_dispatch_targeted_user_ids(uow):
    user = _user()
    uow.users.get_by_id.return_value = user

    use_case = DispatchNotificationsUseCase(uow)
    result = use_case.execute(
        DispatchNotificationsRequest(
            title="Olá",
            message="Mensagem",
            type="info",
            category="welcome",
            presentation="text",
            html_content=None,
            action_type=None,
            action_label=None,
            action_target=None,
            icon=None,
            metadata=None,
            expires_at=None,
            broadcast=False,
            user_ids=[str(user.id)],
            emails=[],
            role_ids=[],
            group_ids=[],
        )
    )

    assert result.created_count == 1
    assert len(result.notification_ids) == 1
    uow.notifications.create.assert_called_once()
    uow.collect_event.assert_called_once()


def test_dispatch_requires_recipients_when_not_broadcast(uow):
    use_case = DispatchNotificationsUseCase(uow)

    with pytest.raises(DispatchNotificationsValidationError):
        use_case.execute(
            DispatchNotificationsRequest(
                title=None,
                message="Sem destinatário",
                type="info",
                category="system",
                presentation="text",
                html_content=None,
                action_type=None,
                action_label=None,
                action_target=None,
                icon=None,
                metadata=None,
                expires_at=None,
                broadcast=False,
                user_ids=[],
                emails=[],
            )
        )


def test_dispatch_broadcast_active_users_only(uow):
    active = _user(email="active@delpi.com", active=True)
    inactive = _user(email="inactive@delpi.com", active=False)
    uow.users.list_all.return_value = [active, inactive]

    use_case = DispatchNotificationsUseCase(uow)
    result = use_case.execute(
        DispatchNotificationsRequest(
            title="Geral",
            message="Para todos",
            type="warning",
            category="announcement",
            presentation="text",
            html_content=None,
            action_type=None,
            action_label=None,
            action_target=None,
            icon=None,
            metadata=None,
            expires_at=None,
            broadcast=True,
            user_ids=[],
            emails=[],
            role_ids=[],
            group_ids=[],
        )
    )

    assert result.created_count == 1
    uow.notifications.create.assert_called_once()


def test_dispatch_controle_mp_skips_user_without_app_access(uow):
    from app.domain.ports.app_query_port import AppDTO, RouteDTO

    allowed = _user(email="allowed@delpi.com")
    denied = _user(email="denied@delpi.com")
    app = AppDTO(
        id="controle-mp",
        name="Controle MP",
        base_path="/controle-mp",
        icon=None,
        type="iframe",
        entry_url="https://x",
        render_mode="embedded",
        routes=[
            RouteDTO(
                path="/controle-mp",
                label="Abrir",
                icon=None,
                permission_code="controle-mp.access",
                show_in_menu=True,
                order=1,
                entry=None,
            )
        ],
    )
    uow.app_queries.list_active_apps_with_routes.return_value = [app]

    def get_user(uid):
        if uid == allowed.id:
            return allowed
        if uid == denied.id:
            return denied
        return None

    uow.users.get_by_id.side_effect = get_user

    with patch(
        "app.application.use_cases.dispatch_notifications_use_case.filter_user_ids_with_app_access"
    ) as filter_access:
        filter_access.return_value = [str(allowed.id)]

        use_case = DispatchNotificationsUseCase(uow)
        result = use_case.execute(
            DispatchNotificationsRequest(
                title="Controle MP",
                message="Nova mensagem",
                type="info",
                category="controle_mp",
                presentation="text",
                html_content=None,
                action_type="portal_route",
                action_label="Abrir",
                action_target="/controle-mp",
                icon=None,
                metadata={"source": "controle_mp", "deepPath": "/conversations/1"},
                expires_at=None,
                broadcast=False,
                user_ids=[],
                emails=[allowed.email, denied.email],
                role_ids=[],
                group_ids=[],
                source_app="controle_mp",
            )
        )

    assert result.created_count == 1
    filter_access.assert_called_once()


def test_dispatch_welcome_template_uses_recipient_name(uow):
    user = _user(name="Ana Paula")
    uow.users.get_by_id.return_value = user

    use_case = DispatchNotificationsUseCase(uow)
    result = use_case.execute(
        DispatchNotificationsRequest(
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
            broadcast=False,
            user_ids=[str(user.id)],
            emails=[],
            role_ids=[],
            group_ids=[],
        )
    )

    assert result.created_count == 1
    created = uow.notifications.create.call_args[0][0]
    assert "Ana" in created.message
    assert created.metadata["vars"]["userName"] == "Ana"
