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
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access

router = APIRouter(prefix="/playlists/{playlist_id}/media", tags=["Media"])
_media_repo = MediaRepository()
_storage = MediaStorageService()


@router.post("")
async def upload_media(request: Request, playlist_id: UUID, file: UploadFile = File(...)):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
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


@router.get("")
def list_media(request: Request, playlist_id: UUID, media_kind: str | None = None):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    kind = media_kind.strip() if isinstance(media_kind, str) and media_kind.strip() else None
    if kind and kind not in {"image", "video", "font"}:
        return fail(message("mediaKindInvalid", "Tipo de mídia inválido."), 422)
    items = _media_repo.list_for_playlist(playlist_id, media_kind=kind)
    return ok({"items": items})


@router.get("/{asset_id}")
def serve_media(request: Request, playlist_id: UUID, asset_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
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
