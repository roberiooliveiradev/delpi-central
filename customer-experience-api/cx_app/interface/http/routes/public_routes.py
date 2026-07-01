from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from cx_app.application.services.feedback_service import (
    FeedbackAlreadyExistsError,
    FeedbackValidationError,
)
from cx_app.application.services.participant_service import ParticipantNotFoundError
from cx_app.composition.cx_composer import build_feedback_service, build_participant_service
from cx_app.core.responses import fail, ok
from cx_app.domain.feedback import FeedbackInput

# Superfície pública (sem login) — consumida pelo shell público (public-hub).
router = APIRouter(prefix="/public/participants", tags=["Public"])


class FeedbackPayload(BaseModel):
    rating: int = Field(ge=1, le=5)
    likedMost: str | None = Field(default=None, max_length=2000)
    suggestions: str | None = Field(default=None, max_length=2000)


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


@router.get("/{token}/feedback")
def get_feedback_status(token: str):
    try:
        data = build_feedback_service().get_status(token)
    except ParticipantNotFoundError:
        return fail("Página não encontrada.", 404)
    return ok(data, message="OK")


@router.post("/{token}/feedback")
def submit_feedback(token: str, payload: FeedbackPayload):
    try:
        data = build_feedback_service().submit(
            token,
            FeedbackInput(
                rating=payload.rating,
                liked_most=payload.likedMost,
                suggestions=payload.suggestions,
            ),
        )
    except ParticipantNotFoundError:
        return fail("Página não encontrada.", 404)
    except FeedbackAlreadyExistsError:
        return fail("Recebemos seu feedback anteriormente. Obrigado!", 409)
    except FeedbackValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Feedback registrado. Obrigado!", status_code=201)
