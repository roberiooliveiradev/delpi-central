from __future__ import annotations

from unittest.mock import patch

from tv_app.application.services.tv_dashboard_portal_notification_service import (
    build_share_granted_copy,
    notify_playlist_share_granted,
    playlist_editor_portal_route,
    role_label,
    tv_dashboard_portal_notifications_enabled,
)


def test_role_label() -> None:
    assert role_label("viewer") == "somente leitura"
    assert role_label("editor") == "editor"


def test_playlist_editor_portal_route() -> None:
    assert playlist_editor_portal_route("abc") == "/apps/tv-dashboard/playlists/abc"


def test_build_share_granted_copy_includes_privilege() -> None:
    title, message = build_share_granted_copy(
        playlist_name="Painel OEE",
        role="editor",
    )
    assert "Acesso concedido" in title
    assert "editor" in message
    assert "Painel OEE" in message


def test_notifications_enabled_requires_core_api() -> None:
    with patch(
        "tv_app.application.services.tv_dashboard_portal_notification_service.settings"
    ) as settings:
        settings.TV_DASHBOARD_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        assert tv_dashboard_portal_notifications_enabled() is True


def test_notifications_disabled_without_token() -> None:
    with patch(
        "tv_app.application.services.tv_dashboard_portal_notification_service.settings"
    ) as settings:
        settings.TV_DASHBOARD_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = ""
        assert tv_dashboard_portal_notifications_enabled() is False


def test_notify_playlist_share_granted_posts_to_core_api() -> None:
    with patch(
        "tv_app.application.services.tv_dashboard_portal_notification_service.settings"
    ) as settings:
        settings.TV_DASHBOARD_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"

        with patch(
            "tv_app.application.services.tv_dashboard_portal_notification_service.httpx.Client"
        ) as client_cls:
            client = client_cls.return_value.__enter__.return_value
            client.post.return_value.status_code = 201

            sent = notify_playlist_share_granted(
                target_user_id="user-42",
                playlist_id="pl-1",
                playlist_name="Série OEE",
                role="viewer",
                actor_user_id="owner-1",
            )

            assert sent is True
            client.post.assert_called_once()
            args, kwargs = client.post.call_args
            assert args[0] == "http://core-api:8000/integrations/notifications"
            payload = kwargs["json"]
            assert payload["userIds"] == ["user-42"]
            assert "somente leitura" in payload["message"]
            assert payload["action"]["target"] == "/apps/tv-dashboard/playlists/pl-1"
            assert payload["metadata"]["event"] == "playlist_share_granted"


def test_notify_skips_self_target() -> None:
    with patch(
        "tv_app.application.services.tv_dashboard_portal_notification_service.settings"
    ) as settings:
        settings.TV_DASHBOARD_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        assert (
            notify_playlist_share_granted(
                target_user_id="same",
                playlist_id="pl-1",
                playlist_name="X",
                role="editor",
                actor_user_id="same",
            )
            is False
        )
