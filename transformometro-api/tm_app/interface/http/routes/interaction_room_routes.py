from __future__ import annotations

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse
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


class MentionBody(BaseModel):
    user_id: str
    label: str = ""


class PostInteractionMessageBody(BaseModel):
    content: str = Field(..., max_length=MAX_MESSAGE_LENGTH)
    parent_id: str | None = None
    mentions: list[MentionBody] = Field(default_factory=list)

    @field_validator("content")
    @classmethod
    def content_is_plain_text(cls, value: str) -> str:
        return normalize_message_content(value)


class EditInteractionMessageBody(BaseModel):
    content: str = Field(..., max_length=MAX_MESSAGE_LENGTH)

    @field_validator("content")
    @classmethod
    def content_is_plain_text(cls, value: str) -> str:
        return normalize_message_content(value)


class ReactionBody(BaseModel):
    code: str


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
def list_interaction_rooms(request: Request, inbox_filter: str = "all"):
    try:
        return ok(
            {
                "items": [
                    room.to_dict()
                    for room in _rooms.list_rooms(request.state.user, inbox_filter=inbox_filter)
                ]
            }
        )
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
def list_interaction_messages(
    request: Request,
    room_id: str,
    limit: int = 50,
    before_id: str | None = None,
):
    try:
        return ok(
            _rooms.list_messages(
                request.state.user,
                room_id,
                limit=limit,
                before_id=before_id,
            )
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/messages",
    operation_id="post_transformometro_interaction_message",
)
def post_interaction_message(request: Request, room_id: str, body: PostInteractionMessageBody):
    try:
        return ok(
            _rooms.post_message(
                request.state.user,
                room_id,
                body.content,
                parent_id=body.parent_id,
                mentions=[item.model_dump() for item in body.mentions],
            ).to_dict(),
            status_code=201,
        )
    except Exception as exc:
        return _handle(exc)


@router.patch(
    "/interaction-rooms/{room_id}/messages/{message_id}",
    operation_id="patch_transformometro_interaction_message",
)
def patch_interaction_message(
    request: Request,
    room_id: str,
    message_id: str,
    body: EditInteractionMessageBody,
):
    try:
        return ok(_rooms.edit_message(request.state.user, room_id, message_id, body.content).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/interaction-rooms/{room_id}/messages/{message_id}",
    operation_id="delete_transformometro_interaction_message",
)
def delete_interaction_message(request: Request, room_id: str, message_id: str):
    try:
        return ok(_rooms.delete_message(request.state.user, room_id, message_id).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/messages/{message_id}/reactions",
    operation_id="toggle_transformometro_interaction_reaction",
)
def toggle_interaction_reaction(request: Request, room_id: str, message_id: str, body: ReactionBody):
    try:
        return ok(_rooms.toggle_reaction(request.state.user, room_id, message_id, body.code).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/messages/{message_id}/pin",
    operation_id="pin_transformometro_interaction_message",
)
def pin_interaction_message(request: Request, room_id: str, message_id: str):
    try:
        return ok(_rooms.pin_message(request.state.user, room_id, message_id).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/interaction-rooms/{room_id}/messages/{message_id}/pin",
    operation_id="unpin_transformometro_interaction_message",
)
def unpin_interaction_message(request: Request, room_id: str, message_id: str):
    try:
        return ok(_rooms.unpin_message(request.state.user, room_id, message_id).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/read",
    operation_id="mark_transformometro_interaction_room_read",
)
def mark_interaction_room_read(request: Request, room_id: str):
    try:
        _rooms.mark_read(request.state.user, room_id)
        return ok({"room_id": room_id})
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/interaction-rooms/{room_id}/attachments",
    operation_id="list_transformometro_interaction_attachments",
)
def list_interaction_attachments(request: Request, room_id: str):
    try:
        return ok({"items": [item.to_dict() for item in _rooms.list_attachments(request.state.user, room_id)]})
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/messages/{message_id}/attachments",
    operation_id="upload_transformometro_interaction_attachment",
)
async def upload_interaction_attachment(
    request: Request,
    room_id: str,
    message_id: str,
    file: UploadFile = File(...),
):
    content = await file.read()
    try:
        saved = _rooms.add_attachment(
            request.state.user,
            room_id,
            message_id,
            file_name=file.filename or "arquivo",
            content=content,
            mime_type=file.content_type,
        )
        return ok(saved.to_dict(), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/interaction-rooms/{room_id}/attachments/{attachment_id}",
    operation_id="download_transformometro_interaction_attachment",
)
def download_interaction_attachment(request: Request, room_id: str, attachment_id: str):
    try:
        path, name, mime = _rooms.open_attachment(request.state.user, room_id, attachment_id)
    except Exception as exc:
        return _handle(exc)
    return FileResponse(path, media_type=mime or "application/octet-stream", filename=name)


@router.delete(
    "/interaction-rooms/{room_id}/attachments/{attachment_id}",
    operation_id="delete_transformometro_interaction_attachment",
)
def delete_interaction_attachment(request: Request, room_id: str, attachment_id: str):
    try:
        _rooms.delete_attachment(request.state.user, room_id, attachment_id)
        return ok({"id": attachment_id})
    except Exception as exc:
        return _handle(exc)
