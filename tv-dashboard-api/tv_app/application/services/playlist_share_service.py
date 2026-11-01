"""Playlist share & edit-invite commands — B5 boundary service.

Keeps concrete persistence adapters out of the gpt_actions facade.
Delegates to the canonical PlaylistRepository methods used by the REST
routes and emits the same domain notifications.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistRepository,
)
from tv_app.application.services.playlist_access_service import (
    PlaylistAccessService,
)
from tv_app.application.services.tv_dashboard_portal_notification_service import (
    notify_playlist_share_granted,
)
from tv_app.application.services.presentation_change_notifier import (
    notify_playlist_library_changed,
)

__all__ = [
    "ShareNotFoundError",
    "assert_can_manage",
    "list_shares",
    "upsert_share",
    "revoke_share",
    "create_edit_invite",
    "revoke_edit_invites",
    "redeem_edit_invite",
]


class ShareNotFoundError(LookupError):
    """Share/invite alvo não existe."""


def assert_can_manage(playlist_id: UUID, user: Any) -> None:
    access = PlaylistAccessService().resolve(playlist_id, user)
    if not access.can_manage:
        raise PermissionError(
            "Você não tem permissão para gerenciar esta programação."
        )


def list_shares(playlist_id: UUID, user: Any) -> list[dict[str, Any]]:
    assert_can_manage(playlist_id, user)
    return PlaylistRepository().list_shares(playlist_id)


def upsert_share(
    playlist_id: UUID,
    user: Any,
    *,
    target_user_id: str,
    role: str,
) -> dict[str, Any]:
    assert_can_manage(playlist_id, user)
    actor = PlaylistAccessService.actor_id(user)
    target = str(target_user_id or "").strip()
    if not target:
        raise ValueError("Informe o usuário de destino.")
    if actor and target == actor:
        raise PermissionError(
            "Não é possível compartilhar consigo mesmo."
        )
    share = PlaylistRepository().upsert_share(
        playlist_id,
        target_user_id=target,
        role=role,
        created_by=actor,
    )
    playlist = PlaylistRepository().get_by_id(playlist_id) or {}
    notify_playlist_share_granted(
        target_user_id=target,
        playlist_id=playlist_id,
        playlist_name=str(playlist.get("name") or ""),
        role=role,
        actor_user_id=actor,
    )
    notify_playlist_library_changed(
        user_ids=[target] + ([actor] if actor else []),
        reason="shared",
        playlist_id=str(playlist_id),
    )
    return share


def revoke_share(playlist_id: UUID, user: Any, *, target_user_id: str) -> None:
    assert_can_manage(playlist_id, user)
    revoked = PlaylistRepository().revoke_share(playlist_id, target_user_id)
    if not revoked:
        raise ShareNotFoundError("Compartilhamento não encontrado.")


def create_edit_invite(
    playlist_id: UUID,
    user: Any,
    *,
    role: str,
) -> dict[str, Any]:
    assert_can_manage(playlist_id, user)
    actor = PlaylistAccessService.actor_id(user)
    if not actor:
        raise PermissionError("Usuário não identificado.")
    invite = PlaylistRepository().create_edit_invite(
        playlist_id, role=role, created_by=actor
    )
    invite["redeemPath"] = (
        f"/apps/tv-dashboard/playlists/{playlist_id}"
        f"/accept-invite?token={invite['token']}"
    )
    return invite


def revoke_edit_invites(playlist_id: UUID, user: Any) -> int:
    assert_can_manage(playlist_id, user)
    return PlaylistRepository().revoke_edit_invites(playlist_id)


def redeem_edit_invite(token: str, user: Any) -> dict[str, Any]:
    actor = PlaylistAccessService.actor_id(user)
    if not actor:
        raise PermissionError("Usuário não identificado.")
    result = PlaylistRepository().redeem_edit_invite(
        token, redeemed_by=actor
    )
    if not result:
        raise ShareNotFoundError("Convite inválido ou revogado.")
    return result
