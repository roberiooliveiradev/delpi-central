# app/tests/test_notification_app_access_service.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.services.notification_app_access_service import (
    filter_user_ids_with_app_access,
    resolve_notification_app_id,
)
from app.domain.ports.app_query_port import AppDTO, RouteDTO
from app.domain.ports.user_repository_port import UserDTO


def _controle_mp_app() -> AppDTO:
    return AppDTO(
        id="controle-mp",
        name="Controle MP",
        base_path="/controle-mp",
        icon="messages-square",
        type="iframe",
        entry_url="https://controle-mp.example",
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


def _user(*, permissions_via_resolver=None, is_superadmin=False):
    uid = uuid4()
    user = UserDTO(
        id=uid,
        email="user@delpi.com",
        name="User",
        active=True,
        is_superadmin=is_superadmin,
        last_login_at=None,
    )
    return user


def test_resolve_app_id_from_source_app_alias():
    uow = MagicMock()
    uow.app_queries.list_active_apps_with_routes.return_value = [_controle_mp_app()]

    app_id = resolve_notification_app_id(
        uow,
        source_app="controle_mp",
        action_target=None,
        metadata=None,
    )

    assert app_id == "controle-mp"


def test_resolve_app_id_from_action_target():
    uow = MagicMock()
    uow.app_queries.list_active_apps_with_routes.return_value = [_controle_mp_app()]

    app_id = resolve_notification_app_id(
        uow,
        source_app=None,
        action_target="/controle-mp/conversations/12",
        metadata={"source": "controle_mp"},
    )

    assert app_id == "controle-mp"


def test_filter_keeps_user_with_app_permission():
    app = _controle_mp_app()
    user = _user()
    other = _user()

    uow = MagicMock()
    uow.app_queries.list_active_apps_with_routes.return_value = [app]
    uow.users.get_by_id.side_effect = lambda uid: (
        user if uid == user.id else (other if uid == other.id else None)
    )

    with patch(
        "app.application.services.notification_app_access_service.PermissionResolver"
    ) as resolver_cls:
        resolver = resolver_cls.return_value
        resolver.resolve.side_effect = lambda uid, is_sa: (
            ["controle-mp.access"] if uid == user.id else []
        )

        result = filter_user_ids_with_app_access(
            uow,
            [str(user.id), str(other.id)],
            source_app="controle_mp",
            action_target="/controle-mp",
            metadata=None,
        )

    assert result == [str(user.id)]


def test_filter_allows_superadmin():
    app = _controle_mp_app()
    admin = _user(is_superadmin=True)

    uow = MagicMock()
    uow.app_queries.list_active_apps_with_routes.return_value = [app]
    uow.users.get_by_id.return_value = admin

    with patch(
        "app.application.services.notification_app_access_service.PermissionResolver"
    ) as resolver_cls:
        resolver_cls.return_value.resolve.return_value = []

        result = filter_user_ids_with_app_access(
            uow,
            [str(admin.id)],
            source_app="controle_mp",
            action_target="/controle-mp",
            metadata=None,
        )

    assert result == [str(admin.id)]


def test_filter_skipped_for_system_notifications_without_app():
    uow = MagicMock()

    result = filter_user_ids_with_app_access(
        uow,
        ["abc"],
        source_app=None,
        action_target=None,
        metadata=None,
    )

    assert result == ["abc"]
    uow.app_queries.list_active_apps_with_routes.assert_not_called()
