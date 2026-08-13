from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends, Path, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_MANAGE_PERMISSIONS,
)
from commercial_app.application.use_cases.manage_commercial_groups import (
    CreateCommercialGroupRequest,
    ManageCommercialGroupsUseCase,
)
from commercial_app.composition.commercial_composer import (
    build_manage_commercial_groups_use_case,
)
from commercial_app.core.auth_actor import actor_sub_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.domain.services.commercial_groups_messages_content_service import (
    CommercialGroupsMessagesContentService,
)
from commercial_app.interface.http.schemas.group_schemas import (
    AddGroupMemberBody,
    CreateCommercialGroupBody,
    ReplaceGroupMembersBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groups", tags=["Commercial groups"])


def _use_case() -> ManageCommercialGroupsUseCase:
    return build_manage_commercial_groups_use_case()


def _current_user_id(request: Request) -> str | None:
    return actor_sub_from_request(request)


@router.get("", operation_id="list_commercial_groups")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def list_commercial_groups(
    _request: Request,
    active_only: bool = Query(default=False),
):
    try:
        use_case = _use_case()
        groups = use_case.list_groups(active_only=active_only)
        return ok(
            {"items": use_case.serialize_groups(groups)},
            message=CommercialGroupsMessagesContentService.message("listOk"),
            operation_id="list_commercial_groups",
        )
    except Exception:
        logger.exception("list_commercial_groups_failed")
        return fail(
            "Erro interno ao listar grupos.",
            500,
            operation_id="list_commercial_groups",
        )


@router.get("/{group_id}", operation_id="get_commercial_group")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def get_commercial_group(
    _request: Request,
    group_id: str = Path(..., min_length=1),
):
    try:
        use_case = _use_case()
        group = use_case.get_group(group_id)
        return ok(
            use_case.serialize_group(group),
            message=CommercialGroupsMessagesContentService.message("getOk"),
            operation_id="get_commercial_group",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="get_commercial_group")
    except Exception:
        logger.exception("get_commercial_group_failed")
        return fail(
            "Erro interno ao carregar grupo.",
            500,
            operation_id="get_commercial_group",
        )


@router.post("", operation_id="create_commercial_group")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def create_commercial_group(
    request: Request,
    body: CreateCommercialGroupBody = Body(...),
):
    try:
        use_case = _use_case()
        group = use_case.create_group(
            CreateCommercialGroupRequest(
                name=body.name,
                kind=body.kind,
                sort_order=body.sort_order,
                active=body.active,
                created_by_user_id=_current_user_id(request),
            )
        )
        return ok(
            use_case.serialize_group(group),
            message=CommercialGroupsMessagesContentService.message("createOk"),
            status_code=201,
            operation_id="create_commercial_group",
        )
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="create_commercial_group")
    except Exception:
        logger.exception("create_commercial_group_failed")
        return fail(
            "Erro interno ao criar grupo.",
            500,
            operation_id="create_commercial_group",
        )


@router.delete("/{group_id}", operation_id="delete_commercial_group")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def delete_commercial_group(
    request: Request,
    group_id: str = Path(..., min_length=1),
):
    try:
        use_case = _use_case()
        use_case.delete_group(
            group_id=group_id,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            {"deleted": True, "id": group_id},
            message=CommercialGroupsMessagesContentService.message("deleteOk"),
            operation_id="delete_commercial_group",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="delete_commercial_group")
    except Exception:
        logger.exception("delete_commercial_group_failed")
        return fail(
            "Erro interno ao excluir grupo.",
            500,
            operation_id="delete_commercial_group",
        )


@router.put("/{group_id}/members", operation_id="replace_commercial_group_members")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def replace_commercial_group_members(
    request: Request,
    group_id: str = Path(..., min_length=1),
    body: ReplaceGroupMembersBody = Body(...),
):
    try:
        use_case = _use_case()
        group = use_case.replace_members(
            group_id=group_id,
            user_ids=body.user_ids,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            use_case.serialize_group(group),
            message=CommercialGroupsMessagesContentService.message("replaceMembersOk"),
            operation_id="replace_commercial_group_members",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="replace_commercial_group_members")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="replace_commercial_group_members")
    except Exception:
        logger.exception("replace_commercial_group_members_failed")
        return fail(
            "Erro interno ao atualizar membros do grupo.",
            500,
            operation_id="replace_commercial_group_members",
        )


@router.post("/{group_id}/members", operation_id="add_commercial_group_member")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def add_commercial_group_member(
    request: Request,
    group_id: str = Path(..., min_length=1),
    body: AddGroupMemberBody = Body(...),
):
    try:
        use_case = _use_case()
        group = use_case.add_member(
            group_id=group_id,
            user_id=body.user_id,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            use_case.serialize_group(group),
            message=CommercialGroupsMessagesContentService.message("addMemberOk"),
            operation_id="add_commercial_group_member",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="add_commercial_group_member")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="add_commercial_group_member")
    except Exception:
        logger.exception("add_commercial_group_member_failed")
        return fail(
            "Erro interno ao adicionar membro ao grupo.",
            500,
            operation_id="add_commercial_group_member",
        )


@router.delete(
    "/{group_id}/members/{user_id}",
    operation_id="remove_commercial_group_member",
)
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def remove_commercial_group_member(
    request: Request,
    group_id: str = Path(..., min_length=1),
    user_id: str = Path(..., min_length=1),
):
    try:
        use_case = _use_case()
        group = use_case.remove_member(
            group_id=group_id,
            user_id=user_id,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            use_case.serialize_group(group),
            message=CommercialGroupsMessagesContentService.message("removeMemberOk"),
            operation_id="remove_commercial_group_member",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="remove_commercial_group_member")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="remove_commercial_group_member")
    except Exception:
        logger.exception("remove_commercial_group_member_failed")
        return fail(
            "Erro interno ao remover membro do grupo.",
            500,
            operation_id="remove_commercial_group_member",
        )
