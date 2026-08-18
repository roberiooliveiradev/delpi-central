from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Body, Path, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_ACCESS_PERMISSIONS,
)
from commercial_app.application.use_cases.manage_interaction_rooms import (
    ResolveInteractionRoomInput,
)
from commercial_app.composition.commercial_composer import (
    build_manage_interaction_rooms_use_case,
)
from commercial_app.core.auth_actor import actor_sub_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from commercial_app.interface.http.schemas.interaction_room_schemas import (
    AddInteractionRoomMemberBody,
    ResolveInteractionRoomBody,
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
