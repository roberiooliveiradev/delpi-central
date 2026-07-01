from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from cx_app.application.services.participant_service import ParticipantNotFoundError
from cx_app.composition.cx_composer import build_participant_service
from cx_app.core.responses import fail, ok

# Superfície pública (sem login) — consumida pelo shell público (public-hub).
router = APIRouter(prefix="/public/participants", tags=["Public"])


@router.get("/{token}")
def get_public_participant(token: str):
    try:
        data = build_participant_service().get_public(token)
    except ParticipantNotFoundError:
        return fail("Página não encontrada.", 404)
    return ok(data, message="OK")


@router.get("/{token}/photo")
def get_public_photo(token: str):
    result = build_participant_service().read_photo_by_token(token)
    if result is None:
        return fail("Foto não encontrada.", 404)
    content, mime = result
    return Response(
        content=content,
        media_type=mime,
        headers={"Cache-Control": "public, max-age=300"},
    )
