"""HTTP routes — lançamento-notas-fiscais."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

from delpi_auth.authz_core import has_permission
from delpi_auth.authorization import require_any_permission, require_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    LANCAMENTO_NOTAS_FISCAIS_ACCESS,
    LANCAMENTO_NOTAS_FISCAIS_CREATE,
    LANCAMENTO_NOTAS_FISCAIS_CREATE_PERMISSIONS,
    LANCAMENTO_NOTAS_FISCAIS_MANAGE,
    LANCAMENTO_NOTAS_FISCAIS_PROCESS,
    LANCAMENTO_NOTAS_FISCAIS_PROCESS_PERMISSIONS,
    LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS,
    LANCAMENTO_NOTAS_FISCAIS_VIEW,
)
from app.application.use_cases.lancamento_notas_fiscais.invoice_posting_use_cases import (
    Actor,
)
from app.composition.lancamento_notas_fiscais_composer import (
    build_add_invoice_posting_comment_use_case,
    build_block_invoice_posting_request_use_case,
    build_cancel_invoice_posting_request_use_case,
    build_create_invoice_posting_request_use_case,
    build_get_invoice_posting_request_use_case,
    build_list_invoice_posting_requests_use_case,
    build_post_manual_invoice_posting_request_use_case,
    build_refresh_invoice_posting_reconciliation_use_case,
    build_resume_invoice_posting_request_use_case,
    build_run_invoice_posting_reconciliation_use_case,
    build_search_suppliers_use_case,
    build_start_invoice_posting_request_use_case,
    build_update_invoice_posting_request_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.lancamento_notas_fiscais.exceptions import InvoicePostingError
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(
    prefix="/lancamento-notas-fiscais",
    tags=["Lançamento de Notas Fiscais"],
)


class CreateRequestBody(BaseModel):
    branch_code: str = Field(..., alias="branch")
    document_number: str = Field(..., alias="document")
    series: str | None = None
    supplier_code: str
    supplier_store: str
    issue_date: str
    amount: float | str
    received_at: str
    observation: str | None = None

    model_config = {"populate_by_name": True}


class BlockBody(BaseModel):
    block_reason: str
    block_description: str


class CancelBody(BaseModel):
    justification: str


class PostManualBody(BaseModel):
    justification: str | None = None


class CommentBody(BaseModel):
    body: str


class ReconciliationRunBody(BaseModel):
    limit: int | None = None


def _actor() -> Actor:
    user = get_current_user()
    if user is None:
        return Actor(user_id="unknown", user_name="Usuário")
    user_id = str(getattr(user, "id", "") or "unknown")
    raw_name = getattr(user, "name", None) or getattr(user, "email", None) or "Usuário"
    return Actor(
        user_id=user_id,
        user_name=format_person_name(str(raw_name)),
        has_access=bool(has_permission(user, LANCAMENTO_NOTAS_FISCAIS_ACCESS)),
        has_create=bool(has_permission(user, LANCAMENTO_NOTAS_FISCAIS_CREATE)),
        has_view=bool(has_permission(user, LANCAMENTO_NOTAS_FISCAIS_VIEW)),
        has_process=bool(has_permission(user, LANCAMENTO_NOTAS_FISCAIS_PROCESS)),
        has_manage=bool(has_permission(user, LANCAMENTO_NOTAS_FISCAIS_MANAGE)),
    )


def _handle_domain(exc: InvoicePostingError):
    meta = getattr(exc, "meta", None) or None
    if exc.status_code == 404:
        return not_found_response(str(exc), code=exc.code)
    return error_response(
        str(exc),
        status_code=exc.status_code,
        code=exc.code,
        recoverable=exc.status_code in {400, 409, 422},
        meta=meta,
    )


@router.get("/suppliers", operation_id="search_lancamento_notas_fiscais_suppliers")
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def search_suppliers(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
):
    try:
        items = build_search_suppliers_use_case().execute(query=query, limit=limit)
        return api_delpi_success(
            {"items": items},
            operation_id="search_lancamento_notas_fiscais_suppliers",
            message="Fornecedores encontrados.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao buscar fornecedores LNF: {exc}")
        return error_response(
            "Erro ao buscar fornecedores.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post("/requests", operation_id="create_lancamento_notas_fiscais_request")
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def create_request(body: CreateRequestBody):
    try:
        data = build_create_invoice_posting_request_use_case().execute(
            body.model_dump(by_alias=False),
            _actor(),
        )
        return api_delpi_success(
            data,
            operation_id="create_lancamento_notas_fiscais_request",
            message="Solicitação criada com sucesso.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao criar solicitação LNF: {exc}")
        return error_response(
            "Erro ao criar solicitação.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.get("/requests", operation_id="list_lancamento_notas_fiscais_requests")
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)
def list_requests(
    branch: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    document: Optional[str] = Query(None),
    issued_from: Optional[str] = Query(None),
    issued_to: Optional[str] = Query(None),
    received_from: Optional[str] = Query(None),
    received_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        filters = {
            "branch": branch,
            "status": status,
            "supplier": supplier,
            "document": document,
            "issued_from": issued_from,
            "issued_to": issued_to,
            "received_from": received_from,
            "received_to": received_to,
        }
        data = build_list_invoice_posting_requests_use_case().execute(
            actor=_actor(),
            filters={k: v for k, v in filters.items() if v},
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(
            data,
            operation_id="list_lancamento_notas_fiscais_requests",
            message="Solicitações listadas com sucesso.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao listar solicitações LNF: {exc}")
        return error_response(
            "Erro ao listar solicitações.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.get(
    "/requests/{request_id}",
    operation_id="get_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)
def get_request(request_id: UUID):
    try:
        data = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        return api_delpi_success(
            data,
            operation_id="get_lancamento_notas_fiscais_request",
            message="Solicitação carregada com sucesso.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao obter solicitação LNF: {exc}")
        return error_response(
            "Erro ao obter solicitação.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.patch(
    "/requests/{request_id}",
    operation_id="update_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE_PERMISSIONS)
def update_request(request_id: UUID, body: dict[str, Any] = Body(...)):
    try:
        data = build_update_invoice_posting_request_use_case().execute(
            str(request_id), body, _actor()
        )
        return api_delpi_success(
            data,
            operation_id="update_lancamento_notas_fiscais_request",
            message="Solicitação atualizada com sucesso.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao atualizar solicitação LNF: {exc}")
        return error_response(
            "Erro ao atualizar solicitação.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/requests/{request_id}/start",
    operation_id="start_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_PROCESS_PERMISSIONS)
def start_request(request_id: UUID):
    try:
        data = build_start_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        return api_delpi_success(
            data,
            operation_id="start_lancamento_notas_fiscais_request",
            message="Atendimento iniciado.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao iniciar solicitação LNF: {exc}")
        return error_response(
            "Erro ao iniciar atendimento.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/requests/{request_id}/block",
    operation_id="block_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_PROCESS_PERMISSIONS)
def block_request(request_id: UUID, body: BlockBody):
    try:
        data = build_block_invoice_posting_request_use_case().execute(
            str(request_id),
            actor=_actor(),
            block_reason=body.block_reason,
            block_description=body.block_description,
        )
        return api_delpi_success(
            data,
            operation_id="block_lancamento_notas_fiscais_request",
            message="Solicitação bloqueada.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao bloquear solicitação LNF: {exc}")
        return error_response(
            "Erro ao bloquear solicitação.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/requests/{request_id}/resume",
    operation_id="resume_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_PROCESS_PERMISSIONS)
def resume_request(request_id: UUID):
    try:
        data = build_resume_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        return api_delpi_success(
            data,
            operation_id="resume_lancamento_notas_fiscais_request",
            message="Atendimento retomado.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao retomar solicitação LNF: {exc}")
        return error_response(
            "Erro ao retomar atendimento.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/requests/{request_id}/comments",
    operation_id="add_lancamento_notas_fiscais_comment",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE_PERMISSIONS)
def add_comment(request_id: UUID, body: CommentBody):
    try:
        data = build_add_invoice_posting_comment_use_case().execute(
            str(request_id), actor=_actor(), body=body.body
        )
        return api_delpi_success(
            data,
            operation_id="add_lancamento_notas_fiscais_comment",
            message="Comentário registrado.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao comentar solicitação LNF: {exc}")
        return error_response(
            "Erro ao registrar comentário.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/requests/{request_id}/cancel",
    operation_id="cancel_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE_PERMISSIONS)
def cancel_request(request_id: UUID, body: CancelBody):
    try:
        data = build_cancel_invoice_posting_request_use_case().execute(
            str(request_id),
            actor=_actor(),
            justification=body.justification,
        )
        return api_delpi_success(
            data,
            operation_id="cancel_lancamento_notas_fiscais_request",
            message="Solicitação cancelada.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao cancelar solicitação LNF: {exc}")
        return error_response(
            "Erro ao cancelar solicitação.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/requests/{request_id}/post-manual",
    operation_id="post_manual_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_PROCESS_PERMISSIONS)
def post_manual_request(
    request_id: UUID,
    body: PostManualBody | None = Body(default=None),
):
    try:
        payload = body or PostManualBody()
        data = build_post_manual_invoice_posting_request_use_case().execute(
            str(request_id),
            actor=_actor(),
            justification=payload.justification,
        )
        return api_delpi_success(
            data,
            operation_id="post_manual_lancamento_notas_fiscais_request",
            message="Solicitação marcada como lançada.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao marcar solicitação LNF como lançada: {exc}")
        return error_response(
            "Erro ao marcar como lançada.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/reconciliation/run",
    operation_id="run_lancamento_notas_fiscais_reconciliation",
)
@require_permission(LANCAMENTO_NOTAS_FISCAIS_MANAGE)
def run_reconciliation(body: ReconciliationRunBody | None = Body(default=None)):
    try:
        payload = body or ReconciliationRunBody()
        data = build_run_invoice_posting_reconciliation_use_case().execute(
            actor=_actor(),
            limit=payload.limit,
        )
        return api_delpi_success(
            data,
            operation_id="run_lancamento_notas_fiscais_reconciliation",
            message="Conciliação executada.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro na conciliação LNF: {exc}")
        return error_response(
            "Erro ao executar conciliação.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.post(
    "/reconciliation/refresh",
    operation_id="refresh_lancamento_notas_fiscais_reconciliation",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)
def refresh_reconciliation():
    try:
        data = build_refresh_invoice_posting_reconciliation_use_case().execute(
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="refresh_lancamento_notas_fiscais_reconciliation",
            message="Atualização da fila solicitada.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro no refresh de conciliação LNF: {exc}")
        return error_response(
            "Erro ao atualizar a fila.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
