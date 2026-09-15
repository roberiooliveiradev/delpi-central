from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel, Field

from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.media_chunked_upload_service import (
    MediaChunkedUploadError,
    MediaChunkedUploadService,
)
from tv_app.application.services.media_storage_service import (
    MediaStorageService,
    MediaValidationError,
)
from tv_app.application.services.media_video_optimize_apply import (
    apply_video_optimize_after_create,
    reoptimize_video_asset,
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
_chunked = MediaChunkedUploadService(storage=_storage)


class MediaUploadSessionBody(BaseModel):
    originalName: str | None = None
    mimeType: str = Field(..., min_length=1)
    sizeBytes: int = Field(..., gt=0)


async def _upload_file_chunks(file: UploadFile):
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        yield chunk


async def _request_body_chunks(request: Request):
    async for chunk in request.stream():
        if chunk:
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
    asset = apply_video_optimize_after_create(
        asset=asset,
        media_repo=_media_repo,
        storage=_storage,
    )
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="media_uploaded",
    )
    return ok(asset, message=message("mediaUploaded", "Mídia enviada."), status_code=201)


@router.post("/uploads", operation_id="create_tv_media_upload_session")
def create_media_upload_session(
    request: Request,
    playlist_id: UUID,
    body: MediaUploadSessionBody,
):
    """Inicia upload em partes (bypass do limite ~100 MB da borda Cloudflare)."""
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    try:
        session = _chunked.create_session(
            playlist_id=str(playlist_id),
            original_name=body.originalName,
            mime_type=body.mimeType,
            size_bytes=body.sizeBytes,
        )
    except MediaValidationError as exc:
        return fail(str(exc), 422)
    except OSError:
        return fail(message("mediaUploadSessionFailed", "Não foi possível iniciar o upload."), 500)
    return ok(session, message=message("mediaUploadSessionCreated", "Sessão de upload criada."), status_code=201)


@router.put(
    "/uploads/{upload_id}/chunks/{chunk_index}",
    operation_id="put_tv_media_upload_chunk",
)
async def put_media_upload_chunk(
    request: Request,
    playlist_id: UUID,
    upload_id: str,
    chunk_index: int,
):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    try:
        result = await _chunked.save_chunk(
            upload_id=upload_id,
            playlist_id=str(playlist_id),
            chunk_index=chunk_index,
            chunks=_request_body_chunks(request),
        )
    except MediaChunkedUploadError as exc:
        return fail(str(exc), 422)
    return ok(result, message=message("mediaUploadChunkSaved", "Parte recebida."))


@router.post(
    "/uploads/{upload_id}/complete",
    operation_id="complete_tv_media_upload_session",
)
async def complete_media_upload_session(
    request: Request,
    playlist_id: UUID,
    upload_id: str,
):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    try:
        stored_name, mime_type, media_kind, size_bytes, original_name = await _chunked.complete(
            upload_id=upload_id,
            playlist_id=str(playlist_id),
        )
    except MediaChunkedUploadError as exc:
        return fail(str(exc), 422)
    except MediaValidationError as exc:
        return fail(str(exc), 422)
    asset = _media_repo.create(
        playlist_id=playlist_id,
        stored_name=stored_name,
        original_name=original_name,
        mime_type=mime_type,
        media_kind=media_kind,
        file_size_bytes=size_bytes,
        created_by=PlaylistAccessService.actor_id(user),
    )
    asset = apply_video_optimize_after_create(
        asset=asset,
        media_repo=_media_repo,
        storage=_storage,
    )
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="media_uploaded",
    )
    return ok(asset, message=message("mediaUploaded", "Mídia enviada."), status_code=201)


@router.delete(
    "/uploads/{upload_id}",
    operation_id="abort_tv_media_upload_session",
)
def abort_media_upload_session(
    request: Request,
    playlist_id: UUID,
    upload_id: str,
):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    try:
        _chunked.abort(upload_id=upload_id, playlist_id=str(playlist_id))
    except MediaChunkedUploadError as exc:
        return fail(str(exc), 404)
    return ok(
        {"uploadId": upload_id, "aborted": True},
        message=message("mediaUploadSessionAborted", "Upload cancelado."),
    )


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


@router.post("/optimize-pending", operation_id="optimize_tv_playlist_videos")
def optimize_playlist_videos(request: Request, playlist_id: UUID):
    """Reprocessa todos os vídeos da playlist ainda sem video_optimized_at."""
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    pending = _media_repo.list_videos_needing_optimize(playlist_id)
    items = []
    for asset in pending:
        try:
            asset_id = UUID(str(asset["id"]))
        except (KeyError, ValueError, TypeError):
            continue
        updated = reoptimize_video_asset(
            playlist_id=playlist_id,
            asset_id=asset_id,
            media_repo=_media_repo,
            storage=_storage,
        )
        if updated:
            items.append(updated)
    if items:
        notify_presentation_changed(
            playlist_id=str(playlist_id),
            reason="media_optimized",
        )
    return ok(
        {"items": items, "optimizedCount": len(items)},
        message=message("mediaPlaylistOptimized", "Vídeos da programação otimizados."),
    )


@router.get("/{asset_id}/poster", operation_id="get_tv_media_poster")
def serve_media_poster(request: Request, playlist_id: UUID, asset_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    asset = _media_repo.get_for_playlist(playlist_id, asset_id)
    if not asset:
        return fail(message("mediaNotFound", "Mídia não encontrada."), 404)
    poster_name = asset.get("posterStoredName")
    if not isinstance(poster_name, str) or not poster_name.strip():
        return fail(message("mediaPosterNotFound", "Poster do vídeo não encontrado."), 404)
    path = _storage.resolve_path(poster_name.strip())
    if path is None:
        return fail(message("mediaPosterNotFound", "Poster do vídeo não encontrado."), 404)
    return build_media_file_response(
        path=path,
        mime_type="image/jpeg",
        range_header=request.headers.get("range"),
    )


@router.post("/{asset_id}/optimize", operation_id="optimize_tv_media_video")
def optimize_media_video(request: Request, playlist_id: UUID, asset_id: UUID):
    """Reprocessa faststart + poster (assets legados ou falha anterior)."""
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    updated = reoptimize_video_asset(
        playlist_id=playlist_id,
        asset_id=asset_id,
        media_repo=_media_repo,
        storage=_storage,
    )
    if not updated:
        return fail(message("mediaNotFound", "Mídia não encontrada."), 404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="media_optimized",
    )
    return ok(updated, message=message("mediaOptimized", "Vídeo otimizado."))


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
    poster = deleted.get("posterStoredName")
    if isinstance(poster, str) and poster.strip():
        _storage.delete(poster.strip())
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="media_deleted",
    )
    return ok(
        {"id": deleted["id"], "deleted": True},
        message=message("mediaDeleted", "Mídia excluída."),
    )
