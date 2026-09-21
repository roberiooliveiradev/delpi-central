from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.use_cases.manage_interaction_rooms import InteractionRoomUseCases
from tm_app.core.responses import fail, ok
from tm_app.domain.services.interaction_room_rules import MAX_MESSAGE_LENGTH, normalize_message_content
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InteractionRoomRepository,
)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro Interaction Rooms"])
_rooms = InteractionRoomUseCases(InteractionRoomRepository())


class OpenInteractionRoomBody(BaseModel):
    processo_id: str


class PostInteractionMessageBody(BaseModel):
    content: str = Field(..., max_length=MAX_MESSAGE_LENGTH)

    @field_validator("content")
    @classmethod
    def content_is_plain_text(cls, value: str) -> str:
        return normalize_message_content(value)


def _handle(exc: Exception):
    if isinstance(exc, AuthorizationDenied):
        return fail(str(exc), exc.status_code)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    if isinstance(exc, RuntimeError) and str(exc) == "OUTCOME_VERIFICATION_FAILED":
        return fail("A gravação não confirmou o estado esperado.", 409)
    raise exc


@router.get("/interaction-rooms", operation_id="list_transformometro_interaction_rooms")
def list_interaction_rooms(request: Request):
    try:
        return ok({"items": [room.to_dict() for room in _rooms.list_rooms(request.state.user)]})
    except Exception as exc:
        return _handle(exc)


@router.post("/interaction-rooms", operation_id="open_transformometro_interaction_room")
def open_interaction_room(request: Request, body: OpenInteractionRoomBody):
    try:
        return ok(_rooms.open_for_process(request.state.user, body.processo_id).to_dict(), status_code=200)
    except Exception as exc:
        return _handle(exc)


@router.get("/interaction-rooms/{room_id}", operation_id="get_transformometro_interaction_room")
def get_interaction_room(request: Request, room_id: str):
    try:
        return ok(_rooms.get_room(request.state.user, room_id).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/interaction-rooms/{room_id}/messages",
    operation_id="list_transformometro_interaction_messages",
)
def list_interaction_messages(request: Request, room_id: str, limit: int = 50):
    try:
        return ok(_rooms.list_messages(request.state.user, room_id, limit=limit))
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/messages",
    operation_id="post_transformometro_interaction_message",
)
def post_interaction_message(request: Request, room_id: str, body: PostInteractionMessageBody):
    try:
        return ok(
            _rooms.post_message(request.state.user, room_id, body.content).to_dict(),
            status_code=201,
        )
    except Exception as exc:
        return _handle(exc)
