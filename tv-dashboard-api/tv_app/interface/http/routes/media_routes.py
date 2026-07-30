from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Request, UploadFile

from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.media_storage_service import (
    MediaStorageService,
    MediaValidationError,
)
from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.core.responses import fail, ok
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository
from tv_app.interface.http.media_file_response import build_media_file_response
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access

router = APIRouter(prefix="/playlists/{playlist_id}/media", tags=["Media"])
_media_repo = MediaRepository()
_storage = MediaStorageService()


async def _upload_file_chunks(file: UploadFile):
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        yield chunk


@router.post("")
async def upload_media(request: Request, playlist_id: UUID, file: UploadFile = File(...)):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    expected: int | None = None
    raw_size = getattr(file, "size", None)
    if isinstance(raw_size, int) and raw_size >= 0:
        expected = raw_size
    try:
        stored_name, mime_type, media_kind, size_bytes = await _storage.save_stream(
            chunks=_upload_file_chunks(file),
            mime_type=file.content_type,
            expected_size=expected,
        )
    except MediaValidationError as exc:
        return fail(str(exc), 422)
    asset = _media_repo.create(
        playlist_id=playlist_id,
        stored_name=stored_name,
        original_name=file.filename,
        mime_type=mime_type,
        media_kind=media_kind,
        file_size_bytes=size_bytes,
        created_by=PlaylistAccessService.actor_id(user),
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
    path = _storage.resolve_path(asset["storedName"])
    if path is None:
        return fail(message("mediaNotFound", "Mídia não encontrada."), 404)
    return build_media_file_response(
        path=path,
        mime_type=asset["mimeType"],
        range_header=request.headers.get("range"),
    )


@router.delete("/{asset_id}")
def delete_media(request: Request, playlist_id: UUID, asset_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    deleted = _media_repo.delete(playlist_id, asset_id)
    if not deleted:
        return fail(message("mediaNotFound", "Mídia não encontrada."), 404)
    _storage.delete(deleted.get("storedName"))
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="media_deleted",
    )
    return ok(
        {"id": deleted["id"], "deleted": True},
        message=message("mediaDeleted", "Mídia excluída."),
    )
