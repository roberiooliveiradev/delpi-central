"""Notificações in-app (sino) do Painéis TV via Core API."""

from __future__ import annotations

import logging
from typing import Any, Literal
from uuid import UUID

import httpx

from tv_app.config import settings

logger = logging.getLogger(__name__)

_SOURCE_APP = "tv-dashboard"
_CATEGORY = "tv_dashboard"
_APP_BASE = "/apps/tv-dashboard"

ShareRole = Literal["viewer", "editor"]


def tv_dashboard_portal_notifications_enabled() -> bool:
    if not settings.TV_DASHBOARD_NOTIFICATIONS_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def playlist_editor_portal_route(playlist_id: str | UUID) -> str:
    return f"{_APP_BASE}/playlists/{playlist_id}"


def role_label(role: str) -> str:
    normalized = (role or "").strip().lower()
    if normalized == "viewer":
        return "somente leitura"
    return "editor"


def build_share_granted_copy(
    *,
    playlist_name: str,
    role: str,
) -> tuple[str, str]:
    privilege = role_label(role)
    title = "Acesso concedido — Painéis TV"
    name = (playlist_name or "").strip() or "uma programação"
    message = (
        f"Você ganhou acesso ({privilege}) à programação «{name}» no Painéis TV. "
        "Abra a programação para visualizar ou editar conforme o privilégio."
    )
    return title, message


def _post_notification(payload: dict[str, Any]) -> bool:
    if not tv_dashboard_portal_notifications_enabled():
        return False

    base_url = settings.CORE_API_BASE_URL.rstrip("/")
    token = settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                f"{base_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code in (200, 201, 202):
            return True
        logger.warning(
            "tv_dashboard_portal_notification_rejected status=%s event=%s",
            response.status_code,
            (payload.get("metadata") or {}).get("event"),
        )
    except Exception:
        logger.warning(
            "tv_dashboard_portal_notification_failed event=%s",
            (payload.get("metadata") or {}).get("event"),
            exc_info=True,
        )
    return False


def notify_playlist_share_granted(
    *,
    target_user_id: str,
    playlist_id: str | UUID,
    playlist_name: str,
    role: str,
    actor_user_id: str | None = None,
) -> bool:
    recipient = (target_user_id or "").strip()
    if not recipient:
        return False
    actor = (actor_user_id or "").strip()
    if actor and actor == recipient:
        return False

    pl_id = str(playlist_id)
    title, message = build_share_granted_copy(playlist_name=playlist_name, role=role)
    privilege = role_label(role)
    target = playlist_editor_portal_route(pl_id)

    payload: dict[str, Any] = {
        "userIds": [recipient],
        "title": title,
        "message": message,
        "type": "info",
        "category": _CATEGORY,
        "sourceApp": _SOURCE_APP,
        "action": {
            "type": "portal_route",
            "label": "Abrir programação",
            "target": target,
        },
        "metadata": {
            "source": _SOURCE_APP,
            "event": "playlist_share_granted",
            "dedupeKey": f"tv-dashboard:share:{pl_id}:{recipient}:{privilege}",
            "playlistId": pl_id,
            "role": (role or "").strip().lower() or "editor",
            "roleLabel": privilege,
        },
    }
    return _post_notification(payload)
