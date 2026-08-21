from __future__ import annotations

import json
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Body, Path, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_ACCESS_PERMISSIONS,
    COMMERCIAL_MANAGE_PERMISSIONS,
    can_manage_portfolios,
    can_use_team_scope,
)
from commercial_app.application.use_cases.create_task_from_interaction_message import (
    CreateTaskFromInteractionMessageInput,
)
from commercial_app.application.use_cases.manage_interaction_messages import (
    PostInteractionMessageInput,
)
from commercial_app.application.use_cases.manage_interaction_rooms import (
    ResolveInteractionRoomInput,
)
from commercial_app.application.services.commercial_realtime_notify import (
    notify_interaction_mention,
    notify_interaction_room_activity,
    notify_interaction_room_deleted,
    notify_room_pin_changed,
    notify_room_reaction_changed,
    notify_worklist_changed,
)
from commercial_app.composition.commercial_composer import (
    build_create_task_from_interaction_message_use_case,
    build_enqueue_task_portal_notifications_service,
    build_list_interaction_inbox_use_case,
    build_list_interaction_room_shared_items_use_case,
    build_manage_interaction_messages_use_case,
    build_manage_interaction_rooms_use_case,
    build_preview_interaction_entity_use_case,
    build_suggest_interaction_mentions_use_case,
)
from commercial_app.core.auth_actor import (
    actor_display_name_from_request,
    actor_sub_from_request,
    current_user_from_request,
)
from commercial_app.core.responses import fail, ok
from commercial_app.interface.http.client_id import client_id_from_request
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from commercial_app.interface.http.schemas.interaction_room_schemas import (
    AddInteractionRoomMemberBody,
    CreateTaskFromInteractionMessageBody,
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


@router.get("", operation_id="list_interaction_rooms")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def list_interaction_rooms(
    request: Request,
    filter: str | None = Query(default="all"),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    operation_id = "list_interaction_rooms"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        filter_value = filter if isinstance(filter, str) else "all"
        query = q if isinstance(q, str) else None
        limit_value = limit if isinstance(limit, int) else 50
        items = build_list_interaction_inbox_use_case().execute(
            actor_user_id=actor,
            filter_key=filter_value,
            query=query,
            limit=limit_value,
        )
        return ok(
            {"items": [item.to_dict() for item in items]},
            message=InteractionRoomContentService.message("listRoomsOk"),
            operation_id=operation_id,
        )
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("list_interaction_rooms_failed")
        return fail("Erro interno ao listar salas.", 500, operation_id=operation_id)


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
            actor_user_id=actor,
            unrestricted=can_manage_portfolios(current_user_from_request(request))
            or can_use_team_scope(current_user_from_request(request)),
        )
        return ok(
            {"items": items},
            message=InteractionRoomContentService.message("suggestOk"),
            operation_id=operation_id,
        )
    except Exception:
        logger.exception("suggest_interaction_mentions_failed")
        return fail("Erro interno ao sugerir menções.", 500, operation_id=operation_id)


@router.get("/entity-preview", operation_id="preview_interaction_entity")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def preview_interaction_entity(
    request: Request,
    kind: str = Query(...),
    ref: str = Query(default="{}"),
):
    operation_id = "preview_interaction_entity"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        kind_value = kind if isinstance(kind, str) else ""
        raw_ref = ref if isinstance(ref, str) else "{}"
        try:
            parsed = json.loads(raw_ref or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(InteractionRoomContentService.error("kindUnknown")) from exc
        if not isinstance(parsed, dict):
            raise ValueError(InteractionRoomContentService.error("kindUnknown"))
        card = build_preview_interaction_entity_use_case().preview(
            kind=kind_value,
            ref=parsed,
            actor_user_id=actor,
            unrestricted=can_manage_portfolios(current_user_from_request(request))
            or can_use_team_scope(current_user_from_request(request)),
        )
        message_key = "previewOk" if card.get("accessible") else "previewDenied"
        return ok(
            card,
            message=InteractionRoomContentService.message(message_key),
            operation_id=operation_id,
        )
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("preview_interaction_entity_failed")
        return fail("Erro interno ao carregar a prévia.", 500, operation_id=operation_id)


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


@router.delete("/{room_id}", operation_id="delete_interaction_room")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def delete_interaction_room(
    request: Request,
    room_id: UUID = Path(...),
):
    operation_id = "delete_interaction_room"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        room = build_manage_interaction_rooms_use_case().soft_delete(
            room_id=room_id,
            actor_user_id=actor,
        )
        try:
            notify_interaction_room_deleted(
                room_id=str(room.id),
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001
            logger.exception("interaction_room_delete_notify_failed")
        return ok(
            room.to_dict(),
            message=InteractionRoomContentService.message("deleteRoomOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("delete_interaction_room_failed")
        return fail("Erro interno ao excluir a sala.", 500, operation_id=operation_id)


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
        try:
            notify_interaction_room_activity(
                reason="created",
                room_id=str(message.room_id),
                message=message,
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
            notify_interaction_mention(
                message=message,
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001 — notificação não pode falhar o POST
            logger.exception("interaction_message_notify_failed")
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
            mentions=_mentions_from_body(body.mentions),
            replace_mentions=body.mentions is not None,
        )
        try:
            notify_interaction_room_activity(
                reason="updated",
                room_id=str(message.room_id),
                message=message,
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
            if body.mentions is not None:
                notify_interaction_mention(
                    message=message,
                    actor_user_id=actor,
                    actor_display_name=actor_display_name_from_request(request),
                    actor_client_id=client_id_from_request(request),
                )
        except Exception:  # noqa: BLE001
            logger.exception("interaction_message_update_notify_failed")
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
        try:
            notify_interaction_room_activity(
                reason="deleted",
                room_id=str(message.room_id),
                message=message,
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001
            logger.exception("interaction_message_delete_notify_failed")
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
        try:
            notify_room_reaction_changed(
                room_id=str(room_id),
                message_id=str(message_id),
                code=reaction.code,
                actor_user_id=actor,
                action="set",
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001
            logger.exception("interaction_reaction_set_notify_failed")
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
        try:
            notify_room_reaction_changed(
                room_id=str(room_id),
                message_id=str(message_id),
                code=code,
                actor_user_id=actor,
                action="clear",
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001
            logger.exception("interaction_reaction_clear_notify_failed")
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


@router.get(
    "/{room_id}/shared-items",
    operation_id="list_interaction_room_shared_items",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def list_interaction_room_shared_items(
    request: Request,
    room_id: UUID = Path(...),
    kind: str = Query(default="all"),
    q: str | None = Query(default=None),
):
    operation_id = "list_interaction_room_shared_items"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        items = build_list_interaction_room_shared_items_use_case().execute(
            room_id=room_id,
            actor_user_id=actor,
            kind=kind if isinstance(kind, str) else "all",
            query=q if isinstance(q, str) else None,
        )
        return ok(
            {"items": items},
            message=InteractionRoomContentService.message("listSharedItemsOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 422, operation_id=operation_id)
    except Exception:
        logger.exception("list_interaction_room_shared_items_failed")
        return fail(
            "Erro interno ao listar itens compartilhados.",
            500,
            operation_id=operation_id,
        )


@router.get("/{room_id}/pins", operation_id="list_interaction_room_pins")
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def list_interaction_room_pins(
    request: Request,
    room_id: UUID = Path(...),
):
    operation_id = "list_interaction_room_pins"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        pins = build_manage_interaction_messages_use_case().list_pins(
            room_id=room_id,
            actor_user_id=actor,
        )
        return ok(
            {"items": [item.to_dict() for item in pins]},
            message=InteractionRoomContentService.message("listPinsOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("list_interaction_room_pins_failed")
        return fail("Erro interno ao listar pins.", 500, operation_id=operation_id)


@router.post(
    "/{room_id}/messages/{message_id}/pin",
    operation_id="pin_interaction_message",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def pin_interaction_message(
    request: Request,
    room_id: UUID = Path(...),
    message_id: UUID = Path(...),
):
    operation_id = "pin_interaction_message"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        pin = build_manage_interaction_messages_use_case().pin(
            room_id=room_id,
            message_id=message_id,
            actor_user_id=actor,
        )
        try:
            notify_room_pin_changed(
                room_id=str(room_id),
                message_id=str(message_id),
                action="set",
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001
            logger.exception("interaction_pin_notify_failed")
        return ok(
            pin.to_dict(),
            message=InteractionRoomContentService.message("pinOk"),
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
        logger.exception("pin_interaction_message_failed")
        return fail("Erro interno ao fixar mensagem.", 500, operation_id=operation_id)


@router.delete(
    "/{room_id}/messages/{message_id}/pin",
    operation_id="unpin_interaction_message",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def unpin_interaction_message(
    request: Request,
    room_id: UUID = Path(...),
    message_id: UUID = Path(...),
):
    operation_id = "unpin_interaction_message"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        cleared = build_manage_interaction_messages_use_case().unpin(
            room_id=room_id,
            message_id=message_id,
            actor_user_id=actor,
        )
        try:
            notify_room_pin_changed(
                room_id=str(room_id),
                message_id=str(message_id),
                action="clear",
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001
            logger.exception("interaction_unpin_notify_failed")
        return ok(
            {"cleared": cleared},
            message=InteractionRoomContentService.message("unpinOk"),
            operation_id=operation_id,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except Exception:
        logger.exception("unpin_interaction_message_failed")
        return fail("Erro interno ao desafixar mensagem.", 500, operation_id=operation_id)


@router.post(
    "/{room_id}/messages/{message_id}/tasks",
    operation_id="create_task_from_interaction_message",
)
@require_any_permission(*COMMERCIAL_ACCESS_PERMISSIONS)
def create_task_from_interaction_message(
    request: Request,
    room_id: UUID = Path(...),
    message_id: UUID = Path(...),
    body: CreateTaskFromInteractionMessageBody | None = Body(default=None),
):
    operation_id = "create_task_from_interaction_message"
    actor, early = _actor_or_401(request, operation_id=operation_id)
    if early is not None:
        return early
    try:
        payload = body or CreateTaskFromInteractionMessageBody()
        result = build_create_task_from_interaction_message_use_case().execute(
            CreateTaskFromInteractionMessageInput(
                room_id=room_id,
                message_id=message_id,
                actor_user_id=actor,
                description=payload.description,
            ),
            actor_is_portfolio_manager=can_manage_portfolios(
                current_user_from_request(request)
            ),
        )
        task = result.task
        try:
            notify_worklist_changed(
                reason="task.created",
                task_id=str(task.id),
                assignee_user_ids=list(task.resolved_assignee_user_ids()),
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                task_title=task.title,
                actor_client_id=client_id_from_request(request),
            )
            build_enqueue_task_portal_notifications_service().on_task_created(
                task=task,
                actor_user_id=actor,
            )
            notify_interaction_room_activity(
                reason="created",
                room_id=str(result.task_ref_message.room_id),
                message=result.task_ref_message,
                actor_user_id=actor,
                actor_display_name=actor_display_name_from_request(request),
                actor_client_id=client_id_from_request(request),
            )
        except Exception:  # noqa: BLE001 — notificação não pode falhar o POST
            logger.exception("task_from_message_notify_failed")
        return ok(
            {
                "task": task.to_dict(),
                "task_ref_message": result.task_ref_message.to_dict(),
            },
            message=InteractionRoomContentService.message("taskFromMessageOk"),
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
        logger.exception("create_task_from_interaction_message_failed")
        return fail(
            "Erro interno ao criar tarefa a partir da mensagem.",
            500,
            operation_id=operation_id,
        )
