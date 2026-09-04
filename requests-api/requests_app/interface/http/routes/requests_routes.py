from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from delpi_auth.request_context import get_current_user

from requests_app.application.errors import ApplicationError
from requests_app.composition.requests_composer import (
    build_create_request_use_case,
    build_file_use_cases,
    build_get_request_type_use_case,
    build_get_request_use_case,
    build_invoice_issuance_lookup_use_cases,
    build_list_my_requests_use_case,
    build_list_request_types_use_case,
    build_list_work_queue_use_case,
    build_timeline_use_cases,
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


class CommentBody(BaseModel):
    body: str = Field(..., min_length=1)


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


@router.get("/request-types/invoice-issuance/lookups/parties")
def lookup_parties(
    party_type: str = Query(..., min_length=1),
    query: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=50),
):
    user = _current_user()
    try:
        data = build_invoice_issuance_lookup_use_cases().search_parties(
            user=user, party_type=party_type, query=query, limit=limit
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/request-types/invoice-issuance/lookups/products")
def lookup_products(
    query: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=50),
):
    user = _current_user()
    try:
        data = build_invoice_issuance_lookup_use_cases().search_products(
            user=user, query=query, limit=limit
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/request-types/invoice-issuance/lookups/carriers")
def lookup_carriers(
    query: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=50),
):
    user = _current_user()
    try:
        data = build_invoice_issuance_lookup_use_cases().search_carriers(
            user=user, query=query, limit=limit
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/request-types/invoice-issuance/lookups/open-sales-orders")
def lookup_open_sales_orders(
    branch: str = Query(..., min_length=2, max_length=2),
    party_code: str = Query(..., min_length=1),
    party_store: str = Query(..., min_length=1),
):
    user = _current_user()
    try:
        data = build_invoice_issuance_lookup_use_cases().list_open_sales_orders(
            user=user,
            branch=branch,
            party_code=party_code,
            party_store=party_store,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/request-types/invoice-issuance/lookups/products/{code}/warehouse-01-balance")
def lookup_warehouse_balance(
    code: str,
    branch: str = Query(..., min_length=2, max_length=2),
):
    user = _current_user()
    try:
        data = build_invoice_issuance_lookup_use_cases().warehouse_balance(
            user=user, product_code=code, branch=branch
        )
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
    q: str | None = Query(default=None, min_length=2),
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
            q=q,
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
    q: str | None = Query(default=None, min_length=2),
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
            q=q,
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


@router.get("/requests/{request_id}/attachments")
def list_attachments(request_id: UUID):
    user = _current_user()
    try:
        data = build_file_use_cases().list_attachments(
            user=user, request_id=str(request_id)
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.post("/requests/{request_id}/attachments")
async def create_attachment(
    request_id: UUID,
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _ = idempotency_key
    user = _current_user()
    content = await file.read()
    try:
        data = build_file_use_cases().upload_attachment(
            user=user,
            request_id=str(request_id),
            original_name=file.filename or "anexo.bin",
            content=content,
            mime_type=file.content_type,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data, message="Anexo enviado.", status_code=201)


@router.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: UUID):
    user = _current_user()
    try:
        path, attachment = build_file_use_cases().resolve_attachment_path(
            user=user, attachment_id=str(attachment_id)
        )
    except ApplicationError as exc:
        return _handle(exc)
    return FileResponse(
        path,
        media_type=attachment.mime_type,
        filename=attachment.original_name,
    )


@router.get("/requests/{request_id}/artifacts")
def list_artifacts(request_id: UUID):
    user = _current_user()
    try:
        data = build_file_use_cases().list_artifacts(
            user=user, request_id=str(request_id)
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.post("/requests/{request_id}/artifacts")
async def create_artifact(
    request_id: UUID,
    file: UploadFile = File(...),
    artifact_kind: str = Form(default="generic"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _ = idempotency_key
    user = _current_user()
    content = await file.read()
    try:
        data = build_file_use_cases().upload_artifact(
            user=user,
            request_id=str(request_id),
            original_name=file.filename or "artefato.bin",
            content=content,
            mime_type=file.content_type,
            artifact_kind=artifact_kind,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data, message="Artefato enviado.", status_code=201)


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: UUID):
    user = _current_user()
    try:
        path, artifact = build_file_use_cases().resolve_artifact_path(
            user=user, artifact_id=str(artifact_id)
        )
    except ApplicationError as exc:
        return _handle(exc)
    return FileResponse(
        path,
        media_type=artifact.mime_type,
        filename=artifact.original_name,
    )


@router.get("/requests/{request_id}/events")
def list_events(
    request_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    user = _current_user()
    try:
        data = build_timeline_use_cases().list_events(
            user=user,
            request_id=str(request_id),
            page=page,
            page_size=page_size,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.get("/requests/{request_id}/comments")
def list_comments(
    request_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    user = _current_user()
    try:
        data = build_timeline_use_cases().list_comments(
            user=user,
            request_id=str(request_id),
            page=page,
            page_size=page_size,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data)


@router.post("/requests/{request_id}/comments")
def create_comment(request_id: UUID, body: CommentBody):
    user = _current_user()
    try:
        data = build_timeline_use_cases().create_comment(
            user=user,
            request_id=str(request_id),
            body=body.body,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data, message="Comentário criado.", status_code=201)