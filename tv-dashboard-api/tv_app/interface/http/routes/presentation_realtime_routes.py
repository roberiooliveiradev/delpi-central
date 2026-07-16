from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketException, status

from delpi_auth.jwt_validator import validate_token
from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.presentation_realtime_hub import presentation_realtime_hub
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository

router = APIRouter(tags=["Presentation Realtime"])
_repo = PlaylistRepository()
_access = PlaylistAccessService()


def _resolve_public_playlist(token: str) -> dict | None:
    playlist = _repo.get_by_token(token.strip())
    if not playlist or not playlist.get("isActive"):
        return None
    return playlist


@router.websocket("/public/present/{token}/ws")
async def public_presentation_ws(websocket: WebSocket, token: str):
    playlist = _resolve_public_playlist(token)
    if not playlist:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    await presentation_realtime_hub.connect(websocket, playlist_id=str(playlist["id"]))


@router.websocket("/playlists/{playlist_id}/presentation-ws")
async def admin_presentation_ws(
    websocket: WebSocket,
    playlist_id: UUID,
    access_token: str | None = None,
):
    auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    token: str | None = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif access_token and access_token.strip():
        token = access_token.strip()
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        user = validate_token(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
    access = _access.resolve(playlist_id, user)
    if not access.can_read:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    await presentation_realtime_hub.connect(websocket, playlist_id=str(playlist_id))
