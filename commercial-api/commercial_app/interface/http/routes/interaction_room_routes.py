from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Body, Path, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_ACCESS_PERMISSIONS,
)
from commercial_app.application.use_cases.manage_interaction_messages import (
    PostInteractionMessageInput,
)
from commercial_app.application.use_cases.manage_interaction_rooms import (
    ResolveInteractionRoomInput,
)
from commercial_app.composition.commercial_composer import (
    build_manage_interaction_messages_use_case,
    build_manage_interaction_rooms_use_case,
    build_suggest_interaction_mentions_use_case,
)
from commercial_app.core.auth_actor import actor_sub_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from commercial_app.interface.http.schemas.interaction_room_schemas import (
    AddInteractionRoomMemberBody,
    PostInteractionMessageBody,
    ResolveInteractionRoomBody,
    UpdateInteractionMessageBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interaction-rooms", tags=["Interaction rooms"])


def _actor_or_401(request: Request, *, operation_id: str):
    actor = actor_sub_from_request(request)
    if not actor:
        return None, fail("Não autenticado.", 401, operation_id=operation_id)
    return actor, None


@router.post("/resolve", operation_id="resolve_interaction_room")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def resolve_interaction_room(
    request: Request,
    body: ResolveInteractionRoomBody = Body(...),
):
    operation_id = "resolve_interaction_room"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        room = build_manage_interaction_rooms_use_case().resolve(
            ResolveInteractionRoomInput(
                kind=body.kind,
                actor_user_id=actor,
                entity_type=body.entity_type,
                entity_key=body.entity_key,
                group_id=body.group_id,
                title=body.title,
            )
        )
        return ok(
            room.to_dict(),
            message=InteractionRoomContentService.message("resolveOk"),
            operation_id=operation_id,
        )
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("resolve_interaction_room_failed")
        return fail("Erro interno ao abrir a sala.", 500, operation_id=operation_id)


@router.get("/mention-suggest", operation_id="suggest_interaction_mentions")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def suggest_interaction_mentions(
    request: Request,
    q: str = Query(default=""),
    kinds: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=20),
):
    operation_id = "suggest_interaction_mentions"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        query = q if isinstance(q, str) else ""
        kind_source = kinds if isinstance(kinds, str) else "user"
        kind_list = [
            item.strip()
            for item in kind_source.split(",")
            if item.strip()
        ]
        items = build_suggest_interaction_mentions_use_case().suggest(
            query=query,
            kinds=kind_list,
            limit=limit if isinstance(limit, int) else 20,
        )
        return ok(
            {"items": items},
            message=InteractionRoomContentService.message("suggestOk"),
            operation_id=operation_id,
        )
    except Exception:
        logger.exception("suggest_interaction_mentions_failed")
        return fail("Erro interno ao sugerir menções.", 500, operation_id=operation_id)


@router.get("/{room_id}", operation_id="get_interaction_room")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def get_interaction_room(
    request: Request,
    room_id: UUID = Path(...),
):
    operation_id = "get_interaction_room"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        room = build_manage_interaction_rooms_use_case().get(
            room_id=room_id,
            actor_user_id=actor,
        )
        return ok(
            room.to_dict(),
            message=InteractionRoomContentService.message("getOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("get_interaction_room_failed")
        return fail("Erro interno ao carregar a sala.", 500, operation_id=operation_id)


@router.get("/{room_id}/members", operation_id="list_interaction_room_members")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def list_interaction_room_members(
    request: Request,
    room_id: UUID = Path(...),
):
    operation_id = "list_interaction_room_members"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        members = build_manage_interaction_rooms_use_case().list_members(
            room_id=room_id,
            actor_user_id=actor,
        )
        return ok(
            {"items": [item.to_dict() for item in members]},
            message=InteractionRoomContentService.message("listMembersOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("list_interaction_room_members_failed")
        return fail("Erro interno ao listar membros.", 500, operation_id=operation_id)


@router.post("/{room_id}/members", operation_id="add_interaction_room_member")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def add_interaction_room_member(
    request: Request,
    room_id: UUID = Path(...),
    body: AddInteractionRoomMemberBody = Body(...),
):
    operation_id = "add_interaction_room_member"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        member = build_manage_interaction_rooms_use_case().add_member(
            room_id=room_id,
            actor_user_id=actor,
            user_id=body.user_id,
            role=body.role,
        )
        return ok(
            member.to_dict(),
            message=InteractionRoomContentService.message("addMemberOk"),
            status_code=201,
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("add_interaction_room_member_failed")
        return fail("Erro interno ao adicionar membro.", 500, operation_id=operation_id)


@router.delete(
    "/{room_id}/members/{user_id}",
    operation_id="remove_interaction_room_member",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def remove_interaction_room_member(
    request: Request,
    room_id: UUID = Path(...),
    user_id: str = Path(..., min_length=1),
):
    operation_id = "remove_interaction_room_member"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        build_manage_interaction_rooms_use_case().remove_member(
            room_id=room_id,
            actor_user_id=actor,
            user_id=user_id,
        )
        return ok(
            {"removed": True, "user_id": user_id},
            message=InteractionRoomContentService.message("removeMemberOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("remove_interaction_room_member_failed")
        return fail("Erro interno ao remover membro.", 500, operation_id=operation_id)


@router.post("/{room_id}/read", operation_id="mark_interaction_room_read")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def mark_interaction_room_read(
    request: Request,
    room_id: UUID = Path(...),
):
    operation_id = "mark_interaction_room_read"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        member = build_manage_interaction_rooms_use_case().mark_read(
            room_id=room_id,
            actor_user_id=actor,
        )
        return ok(
            member.to_dict(),
            message=InteractionRoomContentService.message("markReadOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("mark_interaction_room_read_failed")
        return fail("Erro interno ao marcar leitura.", 500, operation_id=operation_id)


def _mentions_from_body(
    raw: list[dict] | None,
) -> list[tuple[str, dict, str]]:
    items: list[tuple[str, dict, str]] = []
    for entry in raw or []:
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("mention_kind") or entry.get("kind") or "").strip()
        label = str(entry.get("label") or "").strip()
        ref = entry.get("ref")
        if not isinstance(ref, dict):
            ref = {
                key: value
                for key, value in entry.items()
                if key not in {"mention_kind", "kind", "label", "ref"}
            }
        items.append((kind, ref, label))
    return items


@router.get("/{room_id}/messages", operation_id="list_interaction_messages")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def list_interaction_messages(
    request: Request,
    room_id: UUID = Path(...),
    limit: int = Query(default=50, ge=1, le=200),
    before_id: UUID | None = Query(default=None),
    before_created_at: datetime | None = Query(default=None),
    q: str | None = Query(default=None),
):
    operation_id = "list_interaction_messages"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        messages = build_manage_interaction_messages_use_case().list_messages(
            room_id=room_id,
            actor_user_id=actor,
            limit=limit,
            before_created_at=before_created_at,
            before_id=before_id,
            query=q,
        )
        return ok(
            {"items": [item.to_dict() for item in messages]},
            message=InteractionRoomContentService.message("listMessagesOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("list_interaction_messages_failed")
        return fail("Erro interno ao listar mensagens.", 500, operation_id=operation_id)


@router.post("/{room_id}/messages", operation_id="post_interaction_message")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def post_interaction_message(
    request: Request,
    room_id: UUID = Path(...),
    body: PostInteractionMessageBody = Body(...),
):
    operation_id = "post_interaction_message"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        message = build_manage_interaction_messages_use_case().post(
            PostInteractionMessageInput(
                room_id=room_id,
                actor_user_id=actor,
                body_text=body.body_text,
                message_kind=body.message_kind,
                parent_id=body.parent_id,
                mentions=_mentions_from_body(body.mentions),
            )
        )
        return ok(
            message.to_dict(),
            message=InteractionRoomContentService.message("postOk"),
            status_code=201,
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("post_interaction_message_failed")
        return fail("Erro interno ao enviar mensagem.", 500, operation_id=operation_id)


@router.patch(
    "/{room_id}/messages/{message_id}",
    operation_id="update_interaction_message",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def update_interaction_message(
    request: Request,
    room_id: UUID = Path(...),
    message_id: UUID = Path(...),
    body: UpdateInteractionMessageBody = Body(...),
):
    operation_id = "update_interaction_message"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        message = build_manage_interaction_messages_use_case().update(
            room_id=room_id,
            message_id=message_id,
            actor_user_id=actor,
            body_text=body.body_text,
        )
        return ok(
            message.to_dict(),
            message=InteractionRoomContentService.message("updateOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("update_interaction_message_failed")
        return fail("Erro interno ao atualizar mensagem.", 500, operation_id=operation_id)


@router.delete(
    "/{room_id}/messages/{message_id}",
    operation_id="delete_interaction_message",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def delete_interaction_message(
    request: Request,
    room_id: UUID = Path(...),
    message_id: UUID = Path(...),
):
    operation_id = "delete_interaction_message"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        message = build_manage_interaction_messages_use_case().delete(
            room_id=room_id,
            message_id=message_id,
            actor_user_id=actor,
        )
        return ok(
            message.to_dict(),
            message=InteractionRoomContentService.message("deleteOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("delete_interaction_message_failed")
        return fail("Erro interno ao excluir mensagem.", 500, operation_id=operation_id)


@router.put(
    "/{room_id}/messages/{message_id}/reactions/{code}",
    operation_id="set_interaction_message_reaction",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def set_interaction_message_reaction(
    request: Request,
    room_id: UUID = Path(...),
    message_id: UUID = Path(...),
    code: str = Path(..., min_length=1),
):
    operation_id = "set_interaction_message_reaction"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        reaction = build_manage_interaction_messages_use_case().set_reaction(
            room_id=room_id,
            message_id=message_id,
            actor_user_id=actor,
            code=code,
        )
        return ok(
            reaction.to_dict(),
            message=InteractionRoomContentService.message("reactionSetOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("set_interaction_message_reaction_failed")
        return fail("Erro interno ao registrar reação.", 500, operation_id=operation_id)


@router.delete(
    "/{room_id}/messages/{message_id}/reactions/{code}",
    operation_id="clear_interaction_message_reaction",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def clear_interaction_message_reaction(
    request: Request,
    room_id: UUID = Path(...),
    message_id: UUID = Path(...),
    code: str = Path(..., min_length=1),
):
    operation_id = "clear_interaction_message_reaction"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        build_manage_interaction_messages_use_case().clear_reaction(
            room_id=room_id,
            message_id=message_id,
            actor_user_id=actor,
            code=code,
        )
        return ok(
            {"cleared": True, "code": code},
            message=InteractionRoomContentService.message("reactionClearedOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("clear_interaction_message_reaction_failed")
        return fail("Erro interno ao remover reação.", 500, operation_id=operation_id)
