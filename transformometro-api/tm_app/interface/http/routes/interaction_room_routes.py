from __future__ import annotations

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.use_cases.manage_interaction_rooms import InteractionRoomUseCases
from tm_app.core.responses import fail, ok
from tm_app.domain.services.interaction_room_access_service import (
    PrimaryLinkConflict,
    RoomAccessExpansionBlocked,
    RoomAnchorLinkRemovalLocked,
    RoomAuthorizationDenied,
)
from tm_app.domain.services.interaction_room_rules import MAX_MESSAGE_LENGTH, normalize_message_content
from tm_app.infrastructure.gateways.helpdesk_bff_gateway import HelpdeskBffGateway
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InteractionRoomRepository,
)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro Interaction Rooms"])
_rooms = InteractionRoomUseCases(
    InteractionRoomRepository(),
    ticket_visibility=HelpdeskBffGateway(),
    audit=AuditRepository(),
)


class OpenInteractionRoomBody(BaseModel):
    processo_id: str


class OpenTicketRoomBody(BaseModel):
    ticket_id: str = Field(..., min_length=1)


class StandaloneRoomBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    participant_ids: list[str] = Field(default_factory=list)


class AddRoomLinkBody(BaseModel):
    entity_type: str
    entity_key: str = Field(..., min_length=1)
    link_role: str = "reference"


class AddRoomParticipantBody(BaseModel):
    user_id: str = Field(..., min_length=1)


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


def _authorization(request: Request) -> str:
    """Same-user Bearer — forwarded to the Helpdesk BFF when a link
    authority must be evaluated. Never a service token. Missing header
    degrades to empty → the domain denies safely (session_missing)."""
    headers = getattr(request, "headers", None) or {}
    return str(headers.get("authorization") or "").strip()


def _handle(exc: Exception):
    if isinstance(
        exc,
        (
            RoomAuthorizationDenied,
            RoomAccessExpansionBlocked,
            RoomAnchorLinkRemovalLocked,
            PrimaryLinkConflict,
        ),
    ):
        return fail(str(exc), exc.status_code, {"error_code": exc.error_code})
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
                    for room in _rooms.list_rooms(
                        request.state.user,
                        inbox_filter=inbox_filter,
                        authorization=_authorization(request),
                    )
                ]
            }
        )
    except Exception as exc:
        return _handle(exc)


@router.post("/interaction-rooms", operation_id="open_transformometro_interaction_room")
def open_interaction_room(request: Request, body: OpenInteractionRoomBody):
    try:
        return ok(
            _rooms.open_for_process(
                request.state.user, body.processo_id, authorization=_authorization(request)
            ).to_dict(),
            status_code=200,
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/ticket",
    operation_id="open_transformometro_interaction_room_for_ticket",
)
def open_interaction_room_for_ticket(request: Request, body: OpenTicketRoomBody):
    """`open_or_locate` for a GLPI ticket — the caller's Bearer is
    forwarded to the Helpdesk authority; anything it cannot prove
    visible fails closed."""
    try:
        return ok(
            _rooms.open_for_ticket(
                request.state.user,
                body.ticket_id,
                authorization=_authorization(request),
            ).to_dict(),
            status_code=200,
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/standalone",
    operation_id="create_transformometro_standalone_interaction_room",
)
def create_standalone_interaction_room(request: Request, body: StandaloneRoomBody):
    """Standalone collaboration room — always `members` scope; creator
    becomes the owner participant."""
    try:
        return ok(
            _rooms.open_standalone(
                request.state.user,
                body.title,
                participant_ids=body.participant_ids,
            ).to_dict(),
            status_code=201,
        )
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/interaction-rooms/{room_id}/links",
    operation_id="list_transformometro_interaction_room_links",
)
def list_interaction_room_links(request: Request, room_id: str):
    """Active link metadata — content-authorized surface (entity keys are
    protected context, never exposed to admins without content access)."""
    try:
        return ok(
            {
                "items": _rooms.list_links(
                    request.state.user, room_id, authorization=_authorization(request)
                )
            }
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/links",
    operation_id="add_transformometro_interaction_room_link",
)
def add_interaction_room_link(request: Request, room_id: str, body: AddRoomLinkBody):
    """Administrative write — minimal projection; echoing the caller's
    own link id is enough for read-back."""
    try:
        link = _rooms.add_link(
            request.state.user,
            room_id,
            body.entity_type,
            body.entity_key,
            link_role=body.link_role,
            authorization=_authorization(request),
        )
        return ok({"id": link.id}, status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/interaction-rooms/{room_id}/links/{link_id}",
    operation_id="remove_transformometro_interaction_room_link",
)
def remove_interaction_room_link(request: Request, room_id: str, link_id: str):
    """Administrative write — R-1 expansion rule enforced in the use
    case. Response carries only the tombstoned id."""
    try:
        _rooms.remove_link(request.state.user, room_id, link_id)
        return ok({"id": link_id})
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/interaction-rooms/{room_id}/participants",
    operation_id="list_transformometro_interaction_room_participants",
)
def list_interaction_room_participants(request: Request, room_id: str):
    try:
        return ok(
            {
                "items": _rooms.list_participants(
                    request.state.user, room_id, authorization=_authorization(request)
                )
            }
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/participants",
    operation_id="add_transformometro_interaction_room_participant",
)
def add_interaction_room_participant(
    request: Request, room_id: str, body: AddRoomParticipantBody
):
    try:
        _rooms.add_participant(request.state.user, room_id, body.user_id)
        return ok({"user_id": body.user_id}, status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/interaction-rooms/{room_id}/participants/{user_id}",
    operation_id="remove_transformometro_interaction_room_participant",
)
def remove_interaction_room_participant(request: Request, room_id: str, user_id: str):
    try:
        _rooms.remove_participant(request.state.user, room_id, user_id)
        return ok({"user_id": user_id})
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/interaction-rooms/{room_id}/impact",
    operation_id="get_transformometro_interaction_room_delete_impact",
)
def get_interaction_room_delete_impact(request: Request, room_id: str):
    """Administrative delete preview (R-5) — counts and structural
    metadata only; title, entity keys and content never leak."""
    try:
        return ok(_rooms.delete_impact(request.state.user, room_id))
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/restore",
    operation_id="restore_transformometro_interaction_room",
)
def restore_interaction_room(request: Request, room_id: str):
    """Governed restore — safe projection mirroring the delete contract;
    a conflicting primary claim aborts atomically (409)."""
    try:
        room = _rooms.restore_room(
            request.state.user, room_id, authorization=_authorization(request)
        )
        return ok(
            {
                "id": room.id,
                "deleted_at": room.deleted_at.isoformat() if room.deleted_at else None,
            }
        )
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/interaction-rooms/{room_id}",
    operation_id="delete_transformometro_interaction_room",
)
def delete_interaction_room(request: Request, room_id: str):
    """Administrative delete — safe projection only (R-3/R-5): managers
    without content authorization may delete but must never receive
    title, participants, history preview or protected link keys."""
    try:
        room = _rooms.delete_room(request.state.user, room_id)
        return ok(
            {
                "id": room.id,
                "deleted_at": room.deleted_at.isoformat() if room.deleted_at else None,
            }
        )
    except Exception as exc:
        return _handle(exc)


@router.get("/interaction-rooms/{room_id}", operation_id="get_transformometro_interaction_room")
def get_interaction_room(request: Request, room_id: str):
    try:
        return ok(
            _rooms.get_room(
                request.state.user, room_id, authorization=_authorization(request)
            ).to_dict()
        )
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
                authorization=_authorization(request),
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
                authorization=_authorization(request),
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
        return ok(
            _rooms.edit_message(
                request.state.user, room_id, message_id, body.content,
                authorization=_authorization(request),
            ).to_dict()
        )
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/interaction-rooms/{room_id}/messages/{message_id}",
    operation_id="delete_transformometro_interaction_message",
)
def delete_interaction_message(request: Request, room_id: str, message_id: str):
    try:
        return ok(
            _rooms.delete_message(
                request.state.user, room_id, message_id,
                authorization=_authorization(request),
            ).to_dict()
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/messages/{message_id}/reactions",
    operation_id="toggle_transformometro_interaction_reaction",
)
def toggle_interaction_reaction(request: Request, room_id: str, message_id: str, body: ReactionBody):
    try:
        return ok(
            _rooms.toggle_reaction(
                request.state.user, room_id, message_id, body.code,
                authorization=_authorization(request),
            ).to_dict()
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/messages/{message_id}/pin",
    operation_id="pin_transformometro_interaction_message",
)
def pin_interaction_message(request: Request, room_id: str, message_id: str):
    try:
        return ok(
            _rooms.pin_message(
                request.state.user, room_id, message_id,
                authorization=_authorization(request),
            ).to_dict()
        )
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/interaction-rooms/{room_id}/messages/{message_id}/pin",
    operation_id="unpin_transformometro_interaction_message",
)
def unpin_interaction_message(request: Request, room_id: str, message_id: str):
    try:
        return ok(
            _rooms.unpin_message(
                request.state.user, room_id, message_id,
                authorization=_authorization(request),
            ).to_dict()
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/interaction-rooms/{room_id}/read",
    operation_id="mark_transformometro_interaction_room_read",
)
def mark_interaction_room_read(request: Request, room_id: str):
    try:
        _rooms.mark_read(
            request.state.user, room_id, authorization=_authorization(request)
        )
        return ok({"room_id": room_id})
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/interaction-rooms/{room_id}/attachments",
    operation_id="list_transformometro_interaction_attachments",
)
def list_interaction_attachments(request: Request, room_id: str):
    try:
        return ok(
            {
                "items": [
                    item.to_dict()
                    for item in _rooms.list_attachments(
                        request.state.user, room_id, authorization=_authorization(request)
                    )
                ]
            }
        )
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
            authorization=_authorization(request),
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
        path, name, mime = _rooms.open_attachment(
            request.state.user, room_id, attachment_id,
            authorization=_authorization(request),
        )
    except Exception as exc:
        return _handle(exc)
    return FileResponse(path, media_type=mime or "application/octet-stream", filename=name)


@router.delete(
    "/interaction-rooms/{room_id}/attachments/{attachment_id}",
    operation_id="delete_transformometro_interaction_attachment",
)
def delete_interaction_attachment(request: Request, room_id: str, attachment_id: str):
    try:
        _rooms.delete_attachment(
            request.state.user, room_id, attachment_id,
            authorization=_authorization(request),
        )
        return ok({"id": attachment_id})
    except Exception as exc:
        return _handle(exc)
