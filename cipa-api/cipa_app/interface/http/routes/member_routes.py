from __future__ import annotations

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from cipa_app.application.use_cases.member_service import MemberService
from cipa_app.core.responses import fail, ok

router = APIRouter(prefix="/members", tags=["CIPA Members"])
service = MemberService()


class CreateMemberRequest(BaseModel):
    unit_code: str
    user_id: str
    display_name: str = Field(..., min_length=1, max_length=200)
    role: str
    mandate_start: str
    mandate_end: str | None = None
    sort_order: int = 0


class UpdateMemberRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = None
    mandate_start: str | None = None
    mandate_end: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class EndMemberRequest(BaseModel):
    mandate_end: str | None = None


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    raise exc


@router.get("")
def list_members(
    request: Request,
    unit_code: str = Query(..., description="Código da filial (01 ou 02)"),
    active_on: str | None = Query(
        None, description="Data de vigência (AAAA-MM-DD). Quando informada, retorna só ativos na data."
    ),
    include_inactive: bool = Query(
        False, description="Inclui membros inativos/histórico (ignorado se active_on for informado)."
    ),
):
    try:
        return ok(
            service.list_members(
                request.state.user,
                unit_code=unit_code,
                active_on=active_on,
                include_inactive=include_inactive,
            )
        )
    except Exception as exc:
        return _handle(exc)


@router.post("")
def create_member(request: Request, body: CreateMemberRequest):
    try:
        return ok(service.create_member(request.state.user, body.model_dump()), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.patch("/{member_id}")
def update_member(request: Request, member_id: str, body: UpdateMemberRequest):
    try:
        payload = body.model_dump(exclude_unset=True)
        return ok(service.update_member(request.state.user, member_id, payload))
    except Exception as exc:
        return _handle(exc)


@router.post("/{member_id}/end")
def end_member(request: Request, member_id: str, body: EndMemberRequest | None = None):
    try:
        mandate_end = body.mandate_end if body else None
        return ok(service.end_membership(request.state.user, member_id, mandate_end=mandate_end))
    except Exception as exc:
        return _handle(exc)


@router.delete("/{member_id}")
def delete_member(request: Request, member_id: str):
    try:
        return ok(service.soft_delete(request.state.user, member_id))
    except Exception as exc:
        return _handle(exc)
