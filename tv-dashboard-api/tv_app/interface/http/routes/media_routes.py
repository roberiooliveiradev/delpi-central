from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import Response

from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.media_storage_service import (
    MediaStorageService,
    MediaValidationError,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_READ, TV_WRITE, assert_permission
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/playlists/{playlist_id}/media", tags=["Media"])
_repo = PlaylistRepository()
_media_repo = MediaRepository()
_storage = MediaStorageService()


def _ensure_playlist(playlist_id: UUID) -> bool:
    return _repo.get_by_id(playlist_id) is not None


@router.post("")
async def upload_media(request: Request, playlist_id: UUID, file: UploadFile = File(...)):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail(message("playlistNotFound"), 404)
    content = await file.read()
    try:
        stored_name, mime_type, media_kind = _storage.save(
            content=content,
            mime_type=file.content_type,
        )
    except MediaValidationError as exc:
        return fail(str(exc), 422)
    asset = _media_repo.create(
        playlist_id=playlist_id,
        stored_name=stored_name,
        original_name=file.filename,
        mime_type=mime_type,
        media_kind=media_kind,
        file_size_bytes=len(content),
        created_by=getattr(user, "sub", None) or getattr(user, "preferred_username", None),
    )
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="media_uploaded",
    )
    return ok(asset, message=message("mediaUploaded", "Mídia enviada."), status_code=201)


@router.get("/{asset_id}")
def serve_media(request: Request, playlist_id: UUID, asset_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail(message("playlistNotFound"), 404)
    asset = _media_repo.get_for_playlist(playlist_id, asset_id)
    if not asset:
        return fail(message("mediaNotFound", "Mídia não encontrada."), 404)
    data = _storage.read(asset["storedName"])
    if data is None:
        return fail(message("mediaNotFound", "Mídia não encontrada."), 404)
    return Response(
        content=data,
        media_type=asset["mimeType"],
        headers={"Cache-Control": "public, max-age=86400"},
    )
