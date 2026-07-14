from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.presentation_payload_service import PresentationPayloadService
from tv_app.application.services.presentation_status_service import build_presentation_status
from tv_app.application.services.public_filter_overrides_service import parse_filter_overrides_query
from tv_app.application.services.qr_service import build_public_presentation_url, render_qr_png
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_dashboard_portal_notification_service import (
    notify_playlist_share_granted,
)
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_ADMIN, TV_READ, TV_WRITE, assert_permission, can
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistNotFoundError,
    PlaylistRepository,
)
from tv_app.interface.http.auth_http import resolve_user
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access

router = APIRouter(prefix="/playlists", tags=["Playlists"])
_repo = PlaylistRepository()
_present = PresentationPayloadService()
_access = PlaylistAccessService()


class CreatePlaylistBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class UpdatePlaylistBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    viewportProfile: str | None = None
    transitionStyle: str | None = None
    defaultDurationSec: int | None = Field(default=None, ge=5, le=600)
    globalRefreshSec: int | None = Field(default=None, ge=30, le=3600)
    dataDefaults: dict[str, Any] | None = None
    masterConfig: dict[str, Any] | None = None


class SharePlaylistBody(BaseModel):
    targetUserId: str = Field(min_length=1, max_length=200)
    role: Literal["viewer", "editor"] = "editor"


class CreateEditInviteBody(BaseModel):
    role: Literal["viewer", "editor"] = "editor"


class RedeemEditInviteBody(BaseModel):
    token: str = Field(min_length=8, max_length=200)


def _actor_id(user: Any) -> str | None:
    return _access.actor_id(user)


def _with_public_url(playlist: dict[str, Any]) -> dict[str, Any]:
    playlist["publicUrl"] = _present.build_public_url(playlist["publicToken"])
    return playlist


@router.get("")
def list_playlists(request: Request, limit: int = 50, offset: int = 0):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    actor = _actor_id(user)
    # Sempre segregado por dono/share — não listar tudo para superadmin/admin.
    items = _repo.list_playlists(
        limit=limit,
        offset=offset,
        user_id=actor,
        include_all=False,
    )
    for item in items:
        _with_public_url(item)
        if actor and item.get("ownerUserId") == actor:
            item["accessRole"] = "owner"
        elif actor:
            share = _repo.get_share_role(UUID(item["id"]), actor)
            item["accessRole"] = share or "viewer"
        else:
            item["accessRole"] = "viewer"
    return ok({"items": items, "limit": limit, "offset": offset})


@router.post("")
def create_playlist(request: Request, body: CreatePlaylistBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    created_by = _actor_id(user)
    if not created_by:
        return fail("Usuário não identificado.", 401)
    playlist = _repo.create(
        name=body.name,
        description=body.description,
        created_by=created_by,
    )
    playlist["accessRole"] = "owner"
    return ok(_with_public_url(playlist), message="Programação criada.", status_code=201)


@router.post("/edit-invites/accept")
def accept_edit_invite(request: Request, body: RedeemEditInviteBody):
    """Resgata invite: grava share com o user_id do JWT (não usa e-mail)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    result = _repo.redeem_edit_invite(body.token, redeemed_by=actor)
    if not result:
        return fail("Convite inválido, expirado ou revogado.", 404)
    pl_id_raw = str(result.get("playlistId") or "").strip()
    playlist = _repo.get_by_id(UUID(pl_id_raw)) if pl_id_raw else None
    notify_playlist_share_granted(
        target_user_id=actor,
        playlist_id=pl_id_raw,
        playlist_name=str((playlist or {}).get("name") or ""),
        role=str(result.get("role") or "editor"),
        actor_user_id=None,
    )
    return ok(result, message="Acesso concedido.")


@router.get("/{playlist_id}")
def get_playlist(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    user, access = guarded
    playlist = dict(access.playlist or {})
    playlist["publicUrl"] = _present.build_public_url(playlist["publicToken"])
    playlist["slides"] = _repo.list_slides(playlist_id)
    playlist["accessRole"] = access.level
    return ok(playlist)


@router.get("/{playlist_id}/presentation-status")
def presentation_status(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    _, access = guarded
    return ok(build_presentation_status(access.playlist or {}))


@router.patch("/{playlist_id}")
def update_playlist(request: Request, playlist_id: UUID, body: UpdatePlaylistBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    try:
        playlist = _repo.update(
            playlist_id,
            name=body.name,
            description=body.description,
            viewport_profile=body.viewportProfile,
            transition_style=body.transitionStyle,
            default_duration_sec=body.defaultDurationSec,
            global_refresh_sec=body.globalRefreshSec,
            data_defaults=body.dataDefaults,
            master_config=body.masterConfig,
        )
    except PlaylistNotFoundError:
        return fail(message("playlistNotFound"), 404)
    _with_public_url(playlist)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="playlist_updated",
        revision=playlist.get("updatedAt"),
    )
    return ok(playlist, message="Programação atualizada.")


@router.delete("/{playlist_id}")
def delete_playlist(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    try:
        notify_presentation_changed(
            playlist_id=str(playlist_id),
            reason="playlist_deleted",
        )
        _repo.delete(playlist_id)
    except PlaylistNotFoundError:
        return fail(message("playlistNotFound"), 404)
    return ok(message="Programação excluída.")


@router.post("/{playlist_id}/deactivate")
def deactivate_playlist(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    try:
        playlist = _repo.set_active(playlist_id, is_active=False)
    except PlaylistNotFoundError:
        return fail(message("playlistNotFound"), 404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="playlist_deactivated",
        revision=playlist.get("updatedAt"),
    )
    return ok(playlist, message="Link desativado.")


@router.post("/{playlist_id}/activate")
def activate_playlist(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    try:
        playlist = _repo.set_active(playlist_id, is_active=True)
    except PlaylistNotFoundError:
        return fail(message("playlistNotFound"), 404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="playlist_activated",
        revision=playlist.get("updatedAt"),
    )
    return ok(playlist, message="Link reativado.")


@router.get("/{playlist_id}/preview-payload")
def preview_payload(
    request: Request,
    playlist_id: UUID,
    filters: str | None = Query(default=None, description="JSON { slide, bySourceId }"),
):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    user, _access_result = guarded
    auth = request.headers.get("Authorization")
    df_params: dict[str, str] = {}
    for key, value in request.query_params.multi_items():
        if key.startswith("df.") and len(key) > 3:
            df_params[key[3:]] = value
    filter_overrides = parse_filter_overrides_query(filters, df_params or None)
    try:
        payload = _present.build_by_id(
            playlist_id,
            authorization=auth,
            user=user,
            filter_overrides=filter_overrides,
        )
    except PlaylistNotFoundError:
        return fail(message("playlistNotFound"), 404)
    return ok(payload)


@router.get("/{playlist_id}/public-url")
def public_url(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    _, access = guarded
    playlist = access.playlist or {}
    return ok(
        {
            "publicToken": playlist["publicToken"],
            "publicUrl": _present.build_public_url(playlist["publicToken"]),
            "isActive": playlist["isActive"],
        }
    )


@router.get("/{playlist_id}/qr")
def download_qr(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    _, access = guarded
    playlist = access.playlist or {}
    url = build_public_presentation_url(playlist["publicToken"])
    png = render_qr_png(url)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="tv-dashboard-{playlist_id}.png"'},
    )


@router.post("/{playlist_id}/duplicate")
def duplicate_playlist(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    created_by = _actor_id(user)
    if not created_by:
        return fail("Usuário não identificado.", 401)
    try:
        playlist = _repo.duplicate_playlist(playlist_id, created_by=created_by)
    except PlaylistNotFoundError:
        return fail(message("playlistNotFound"), 404)
    _with_public_url(playlist)
    playlist["slides"] = _repo.list_slides(UUID(playlist["id"]))
    playlist["accessRole"] = "owner"
    return ok(playlist, message="Programação duplicada.", status_code=201)


@router.post("/{playlist_id}/regenerate-token")
def regenerate_token(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    try:
        playlist = _repo.regenerate_token(playlist_id)
    except PlaylistNotFoundError:
        return fail(message("playlistNotFound"), 404)
    _with_public_url(playlist)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="token_regenerated",
        revision=playlist.get("updatedAt"),
    )
    return ok(
        playlist,
        message="Novo link gerado. O link anterior deixou de funcionar.",
    )


# --- Compartilhamento (sempre target_user_id; e-mail só resolve no cliente) ---


@router.get("/{playlist_id}/shares")
def list_shares(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    return ok({"items": _repo.list_shares(playlist_id)})


@router.post("/{playlist_id}/shares")
def upsert_share(request: Request, playlist_id: UUID, body: SharePlaylistBody):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    user, access = guarded
    actor = _actor_id(user)
    target = body.targetUserId.strip()
    if not target:
        return fail("Informe o usuário de destino.", 422)
    if actor and target == actor:
        return fail("Não é possível compartilhar consigo mesmo.", 422)
    share = _repo.upsert_share(
        playlist_id,
        target_user_id=target,
        role=body.role,
        created_by=actor,
    )
    playlist = (access.playlist if access else None) or _repo.get_by_id(playlist_id) or {}
    notify_playlist_share_granted(
        target_user_id=target,
        playlist_id=playlist_id,
        playlist_name=str(playlist.get("name") or ""),
        role=body.role,
        actor_user_id=actor,
    )
    return ok(share, message="Compartilhamento atualizado.")


@router.delete("/{playlist_id}/shares/{target_user_id}")
def revoke_share(request: Request, playlist_id: UUID, target_user_id: str):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    revoked = _repo.revoke_share(playlist_id, target_user_id)
    if not revoked:
        return fail("Compartilhamento não encontrado.", 404)
    return ok(message="Compartilhamento removido.")


@router.post("/{playlist_id}/edit-invites")
def create_edit_invite(request: Request, playlist_id: UUID, body: CreateEditInviteBody):
    """Gera link de edição: quem abrir (logado) recebe share atrelado ao próprio user_id."""
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    invite = _repo.create_edit_invite(playlist_id, role=body.role, created_by=actor)
    # Path do MFE — o hub autenticado resgata o token.
    invite["redeemPath"] = f"/apps/tv-dashboard/playlists/{playlist_id}/accept-invite?token={invite['token']}"
    return ok(invite, message="Link de edição gerado.", status_code=201)


@router.post("/{playlist_id}/edit-invites/revoke")
def revoke_edit_invites(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="manage")
    if is_access_error(guarded):
        return guarded
    count = _repo.revoke_edit_invites(playlist_id)
    return ok({"revoked": count}, message="Links de edição revogados.")
