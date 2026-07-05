from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from tv_app.application.services.presentation_payload_service import PresentationPayloadService
from tv_app.application.services.qr_service import build_public_presentation_url, render_qr_png
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_MANAGE, TV_READ, TV_WRITE, assert_permission
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistNotFoundError,
    PlaylistRepository,
)
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/playlists", tags=["Playlists"])
_repo = PlaylistRepository()
_present = PresentationPayloadService()


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


@router.get("")
def list_playlists(request: Request, limit: int = 50, offset: int = 0):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = _repo.list_playlists(limit=limit, offset=offset)
    for item in items:
        item["publicUrl"] = _present.build_public_url(item["publicToken"])
    return ok({"items": items, "limit": limit, "offset": offset})


@router.post("")
def create_playlist(request: Request, body: CreatePlaylistBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    created_by = getattr(user, "sub", None) or getattr(user, "preferred_username", None)
    playlist = _repo.create(
        name=body.name,
        description=body.description,
        created_by=created_by,
    )
    playlist["publicUrl"] = _present.build_public_url(playlist["publicToken"])
    return ok(playlist, message="Programação criada.", status_code=201)


@router.get("/{playlist_id}")
def get_playlist(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    playlist = _repo.get_by_id(playlist_id)
    if not playlist:
        return fail("Programação não encontrada.", 404)
    playlist["publicUrl"] = _present.build_public_url(playlist["publicToken"])
    playlist["slides"] = _repo.list_slides(playlist_id)
    return ok(playlist)


@router.patch("/{playlist_id}")
def update_playlist(request: Request, playlist_id: UUID, body: UpdatePlaylistBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        playlist = _repo.update(
            playlist_id,
            name=body.name,
            description=body.description,
            viewport_profile=body.viewportProfile,
            transition_style=body.transitionStyle,
            default_duration_sec=body.defaultDurationSec,
            global_refresh_sec=body.globalRefreshSec,
        )
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", 404)
    playlist["publicUrl"] = _present.build_public_url(playlist["publicToken"])
    return ok(playlist, message="Programação atualizada.")


@router.delete("/{playlist_id}")
def delete_playlist(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        _repo.delete(playlist_id)
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", 404)
    return ok(message="Programação excluída.")


@router.post("/{playlist_id}/deactivate")
def deactivate_playlist(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        playlist = _repo.set_active(playlist_id, is_active=False)
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", 404)
    return ok(playlist, message="Link desativado.")


@router.post("/{playlist_id}/activate")
def activate_playlist(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        playlist = _repo.set_active(playlist_id, is_active=True)
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", 404)
    return ok(playlist, message="Link reativado.")


@router.get("/{playlist_id}/preview-payload")
def preview_payload(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    auth = request.headers.get("Authorization")
    try:
        payload = _present.build_by_id(playlist_id, authorization=auth)
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", 404)
    return ok(payload)


@router.get("/{playlist_id}/public-url")
def public_url(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    playlist = _repo.get_by_id(playlist_id)
    if not playlist:
        return fail("Programação não encontrada.", 404)
    return ok(
        {
            "publicToken": playlist["publicToken"],
            "publicUrl": _present.build_public_url(playlist["publicToken"]),
            "isActive": playlist["isActive"],
        }
    )


@router.get("/{playlist_id}/qr")
def download_qr(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    playlist = _repo.get_by_id(playlist_id)
    if not playlist:
        return fail("Programação não encontrada.", 404)
    url = build_public_presentation_url(playlist["publicToken"])
    png = render_qr_png(url)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="tv-dashboard-{playlist_id}.png"'},
    )


@router.post("/{playlist_id}/duplicate")
def duplicate_playlist(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    created_by = getattr(user, "sub", None) or getattr(user, "preferred_username", None)
    try:
        playlist = _repo.duplicate_playlist(playlist_id, created_by=created_by)
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", 404)
    playlist["publicUrl"] = _present.build_public_url(playlist["publicToken"])
    playlist["slides"] = _repo.list_slides(UUID(playlist["id"]))
    return ok(playlist, message="Programação duplicada.", status_code=201)


@router.post("/{playlist_id}/regenerate-token")
def regenerate_token(request: Request, playlist_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        playlist = _repo.regenerate_token(playlist_id)
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", 404)
    playlist["publicUrl"] = _present.build_public_url(playlist["publicToken"])
    return ok(
        playlist,
        message="Novo link gerado. O link anterior deixou de funcionar.",
    )
