from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from delpi_auth.request_context import get_current_user

from requests_app.application.errors import ApplicationError
from requests_app.composition.requests_composer import (
    build_create_request_use_case,
    build_get_request_type_use_case,
    build_get_request_use_case,
    build_list_my_requests_use_case,
    build_list_request_types_use_case,
    build_list_work_queue_use_case,
    build_transition_request_use_case,
    build_update_request_payload_use_case,
)
from requests_app.core.responses import fail, ok

router = APIRouter(prefix="/v1", tags=["Requests"])


def _current_user():
    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return user


def _handle(exc: ApplicationError):
    return fail(exc.message, status_code=exc.status_code, data={"code": exc.code})


class CreateRequestBody(BaseModel):
    type_code: str = Field(..., min_length=1)
    branch_code: str | None = Field(default=None, alias="branch")
    priority: str = "normal"
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class UpdatePayloadBody(BaseModel):
    payload: dict[str, Any]
    version: int | None = None


class TransitionBody(BaseModel):
    version: int | None = None
    return_reason: str | None = None
    cancel_justification: str | None = None


@router.get("/request-types")
def list_request_types():
    user = _current_user()
    try:
        data = build_list_request_types_use_case().execute(user=user)
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/request-types/{code}")
def get_request_type(code: str):
    user = _current_user()
    try:
        data = build_get_request_type_use_case().execute(user=user, code=code)
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.post("/requests")
def create_request(
    body: CreateRequestBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    user = _current_user()
    try:
        data = build_create_request_use_case().execute(
            user=user,
            type_code=body.type_code,
            payload=body.payload,
            branch_code=body.branch_code,
            priority=body.priority,
            idempotency_key=idempotency_key,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data, message="Solicitação criada.", status_code=201)


@router.get("/requests/mine")
def list_my_requests(
    type_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    user = _current_user()
    try:
        data = build_list_my_requests_use_case().execute(
            user=user,
            type_code=type_code,
            status=status,
            branch_code=branch,
            page=page,
            page_size=page_size,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/requests/work-queue")
def list_work_queue(
    type_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    user = _current_user()
    try:
        data = build_list_work_queue_use_case().execute(
            user=user,
            type_code=type_code,
            status=status,
            branch_code=branch,
            page=page,
            page_size=page_size,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/requests/{request_id}")
def get_request(request_id: UUID):
    user = _current_user()
    try:
        data = build_get_request_use_case().execute(
            user=user, request_id=str(request_id)
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.patch("/requests/{request_id}")
def update_request(
    request_id: UUID,
    body: UpdatePayloadBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    user = _current_user()
    try:
        data = build_update_request_payload_use_case().execute(
            user=user,
            request_id=str(request_id),
            payload=body.payload,
            expected_version=body.version,
            idempotency_key=idempotency_key,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data, message="Solicitação atualizada.")


@router.post("/requests/{request_id}/transitions/{action}")
def transition_request(
    request_id: UUID,
    action: str,
    body: TransitionBody | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    user = _current_user()
    payload = body or TransitionBody()
    transition_body = {
        key: value
        for key, value in {
            "return_reason": payload.return_reason,
            "cancel_justification": payload.cancel_justification,
        }.items()
        if value is not None
    }
    try:
        data = build_transition_request_use_case().execute(
            user=user,
            request_id=str(request_id),
            action=action,
            body=transition_body,
            expected_version=payload.version,
            idempotency_key=idempotency_key,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data, message="Transição aplicada.")
