from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import Response

from tv_app.application.services.media_storage_service import MediaStorageService
from tv_app.application.services.presentation_payload_service import PresentationPayloadService
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.core.responses import fail, ok
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository

router = APIRouter(prefix="/public", tags=["Public"])
_present = PresentationPayloadService()
_repo = PlaylistRepository()
_media_repo = MediaRepository()
_storage = MediaStorageService()


@router.get("/present/{token}/media/{asset_id}")
def public_media(token: str, asset_id: UUID):
    asset = _media_repo.get_for_token(token, asset_id)
    if not asset:
        return fail(message("mediaNotFound"), 404)
    data = _storage.read(asset["storedName"])
    if data is None:
        return fail(message("mediaNotFound"), 404)
    return Response(
        content=data,
        media_type=asset["mimeType"],
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/present/{token}")
def public_present(token: str):
    payload = _present.build_by_token(token, track_view=True)
    if payload is None:
        return fail("Programação não encontrada ou desativada.", 404)
    return ok(payload)


@router.post("/present/{token}/heartbeat")
def public_heartbeat(token: str):
    if not _repo.touch_heartbeat(token):
        return fail("Programação não encontrada ou desativada.", 404)
    return ok({"ok": True})
