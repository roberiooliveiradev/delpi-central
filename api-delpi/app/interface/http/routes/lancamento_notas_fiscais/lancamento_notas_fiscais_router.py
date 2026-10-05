"""HTTP routes — lançamento-notas-fiscais."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Query
from fastapi.responses import Response
from app.interface.http.pagination_query import (
    LIMIT_QUERY,
    PAGE_SIZE_QUERY,
)

from pydantic import BaseModel, Field, field_validator

from delpi_auth.authz_core import has_permission
from delpi_auth.authorization import require_any_permission, require_permission
from delpi_auth.request_context import get_current_user, get_request_authorization

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
from app.application.services.lancamento_notas_fiscais.fiscal_attachment_storage import (
    LancamentoFiscalAttachmentStorage,
    LancamentoFiscalAttachmentStorageError,
)
from app.application.services.lancamento_notas_fiscais.danfe_storage import (
    LancamentoDanfeStorage,
    LancamentoDanfeStorageError,
)
from app.composition.lancamento_notas_fiscais_composer import (
    build_add_invoice_posting_comment_use_case,
    build_block_invoice_posting_request_use_case,
    build_cancel_invoice_posting_request_use_case,
    build_get_invoice_posting_request_use_case,
    build_invoice_posting_request_repository,
    build_list_invoice_posting_requests_use_case,
    build_link_request_purchase_order_use_case,
    build_list_request_open_purchase_orders_use_case,
    build_post_manual_invoice_posting_request_use_case,
    build_financial_received_invoice_gateway,
    build_received_invoice_attachment_service,
    build_refresh_invoice_posting_reconciliation_use_case,
    build_resume_invoice_posting_request_use_case,
    build_run_invoice_posting_reconciliation_use_case,
    build_search_suppliers_use_case,
    build_start_invoice_posting_request_use_case,
    build_update_invoice_posting_request_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.lancamento_notas_fiscais.exceptions import InvoicePostingError
from app.infrastructure.gateways.financial_received_invoice_gateway import (
    FinancialReceivedInvoiceGatewayError,
)
from app.domain.services.lancamento_notas_fiscais.fiscal_normalization import (
    FiscalNormalizationError,
    normalize_branch,
    resolve_list_status_filter,
)
from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_branch_access import (
    branch_access_error,
    has_global_branch_access,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(
    prefix="/lancamento-notas-fiscais",
    tags=["Lançamento de Notas Fiscais"],
)


class LinkedInvoiceBody(BaseModel):
    document_number: str = Field(..., alias="document")
    series: str | None = None

    model_config = {"populate_by_name": True}


class CreateRequestBody(BaseModel):
    branch_code: str = Field(..., alias="branch")
    document_number: str = Field(..., alias="document")
    series: str | None = None
    fiscal_model: str
    supplier_code: str
    supplier_store: str
    issue_date: str
    amount: float | str
    received_at: str
    observation: str | None = None
    source: str | None = None
    document_id: str | None = None
    access_key: str | None = None
    source_branch: str | None = None
    source_document_type: str | None = None
    source_document_id: str | None = None
    provider_document_number: str | None = None
    linked_invoices: list[LinkedInvoiceBody] | None = None
    provider_file_id: str | None = None

    model_config = {"populate_by_name": True}


class BlockBody(BaseModel):
    block_reason: str
    block_description: str
    assignee_user_id: str
    assignee_name: str


class CancelBody(BaseModel):
    justification: str


class PostManualBody(BaseModel):
    justification: str | None = None


class CommentBody(BaseModel):
    body: str
    mentioned_user_ids: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("mentioned_user_ids")
    @classmethod
    def _normalize_mentioned_user_ids(cls, value: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for raw in value or []:
            uid = str(raw or "").strip()
            if not uid or uid in seen:
                continue
            seen.add(uid)
            unique.append(uid)
        return unique


class LinkPurchaseOrderLineBody(BaseModel):
    order_item: str


class LinkPurchaseOrderGroupBody(BaseModel):
    order_number: str
    delivery_date: str | None = None
    lines: list[LinkPurchaseOrderLineBody] | None = None


class LinkPurchaseOrderBody(BaseModel):
    """Aceita `groups[]` (N) ou body legado com um único order_number."""

    groups: list[LinkPurchaseOrderGroupBody] | None = None
    order_number: str | None = None
    delivery_date: str | None = None


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


def _pdf_response(content: bytes, filename: str, disposition: str) -> Response:
    safe_name = "".join(ch for ch in filename if ch.isalnum() or ch in {".", "-", "_"}) or "danfe.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{safe_name}"'},
    )


def _handle_financial(exc: FinancialReceivedInvoiceGatewayError):
    return error_response(
        str(exc),
        status_code=exc.status_code,
        code="financial_invoices.upstream",
        recoverable=exc.status_code in {403, 422, 503},
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


def _gate_payload_branch(branch_raw: str | None):
    try:
        branch = normalize_branch(branch_raw)
    except FiscalNormalizationError as exc:
        return error_response(
            str(exc),
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    return branch_access_error(branch)


def _gate_loaded_branch(data: dict[str, Any]):
    payload = data.get("request") if isinstance(data.get("request"), dict) else data
    branch = str((payload or {}).get("branch_code") or "").strip()
    if not branch:
        return error_response(
            "Solicitação sem filial.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    return branch_access_error(branch)


@router.get("/suppliers", operation_id="search_lancamento_notas_fiscais_suppliers")
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def search_suppliers(
    query: str = Query(..., min_length=2),
    limit: int = LIMIT_QUERY("limit_20_50"),
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


@router.get(
    "/received-invoices",
    operation_id="list_lancamento_notas_fiscais_received_invoices",
)
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def list_received_invoices(
    invoice_number: str | None = Query(None),
    supplier_cnpj: str | None = Query(None),
    page: int = Query(1),
    page_size: int = Query(25),
    document_type: str | None = Query(None),
):
    number = str(invoice_number or "").strip()
    cnpj = str(supplier_cnpj or "").strip()
    if not number and not cnpj:
        return error_response(
            "Informe o número da nota ou o CNPJ do fornecedor.",
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    if page < 1 or page_size < 1 or page_size > 100:
        return error_response(
            "Paginação inválida.",
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    try:
        data = build_financial_received_invoice_gateway().list_received_invoices(
            authorization=str(get_request_authorization() or ""),
            invoice_number=number or None,
            supplier_cnpj=cnpj or None,
            page=page,
            page_size=page_size,
            document_type=document_type if isinstance(document_type, str) else None,
        )
        return api_delpi_success(
            data,
            operation_id="list_lancamento_notas_fiscais_received_invoices",
            message="Notas fiscais de entrada carregadas.",
        )
    except FinancialReceivedInvoiceGatewayError as exc:
        return _handle_financial(exc)
    except Exception as exc:
        log_error(f"Erro ao consultar NF-e de entrada no lançamento: {type(exc).__name__}")
        return error_response(
            "Erro ao consultar notas fiscais.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )


@router.get(
    "/received-invoices/{document_id}/danfe",
    operation_id="get_lancamento_notas_fiscais_received_invoice_danfe",
)
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def preview_received_invoice_danfe(
    document_id: str,
    access_key: str = Query(""),
    branch: str = Query(""),
):
    try:
        content, filename = build_financial_received_invoice_gateway().download_danfe(
            authorization=str(get_request_authorization() or ""),
            document_id=document_id,
            access_key=access_key,
            branch=branch,
        )
    except FinancialReceivedInvoiceGatewayError as exc:
        return _handle_financial(exc)
    except Exception as exc:
        log_error(f"Erro ao pré-visualizar DANFE no lançamento: {type(exc).__name__}")
        return error_response(
            "Erro ao obter o DANFE.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    return _pdf_response(content, filename, "inline")


@router.get(
    "/received-invoices/{document_id}/dacte",
    operation_id="get_lancamento_notas_fiscais_received_cte_dacte",
)
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def preview_received_cte_dacte(
    document_id: str,
    file_id: str = Query(""),
    access_key: str = Query(""),
    branch: str = Query(""),
):
    try:
        content, filename = build_financial_received_invoice_gateway().download_dacte(
            authorization=str(get_request_authorization() or ""),
            document_id=document_id,
            file_id=file_id,
            access_key=access_key,
            branch=branch,
        )
    except FinancialReceivedInvoiceGatewayError as exc:
        return _handle_financial(exc)
    except Exception as exc:
        log_error(f"Erro ao pré-visualizar DACTE no lançamento: {type(exc).__name__}")
        return error_response(
            "Erro ao obter o DACTE.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    return _pdf_response(content, filename, "inline")


@router.get(
    "/received-invoices/{document_id}/detail",
    operation_id="get_lancamento_notas_fiscais_received_nfse_detail",
)
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def received_fiscal_detail(
    document_id: str,
    branch: str = Query(""),
    document_type: str = Query("nfse"),
    file_id: str = Query(""),
    access_key: str = Query(""),
):
    kind = str(document_type or "").strip().lower()
    gateway = build_financial_received_invoice_gateway()
    authorization = str(get_request_authorization() or "")
    try:
        if kind == "nfse":
            data = gateway.get_nfse_detail(
                authorization=authorization,
                document_id=document_id,
                branch=branch,
            )
            message = "Dados da NFS-e carregados."
        elif kind == "cte":
            data = gateway.get_cte_detail(
                authorization=authorization,
                document_id=document_id,
                file_id=file_id,
                access_key=access_key,
                branch=branch,
            )
            message = "Dados do CT-e carregados."
        else:
            return error_response(
                "O detalhe estruturado está disponível para NFS-e e CT-e.",
                status_code=422,
                code="VALIDATION_ERROR",
                recoverable=True,
            )
    except FinancialReceivedInvoiceGatewayError as exc:
        return _handle_financial(exc)
    except Exception as exc:
        log_error(f"Erro ao detalhar documento fiscal no lançamento: {type(exc).__name__}")
        return error_response(
            "Erro ao carregar os dados do documento fiscal.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    return api_delpi_success(
        data,
        operation_id="get_lancamento_notas_fiscais_received_nfse_detail",
        message=message,
    )


@router.get(
    "/received-invoices/{document_id}/xml/{variant}",
    operation_id="get_lancamento_notas_fiscais_received_nfse_xml",
)
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def download_received_fiscal_xml(
    document_id: str,
    variant: str,
    branch: str = Query(""),
    document_type: str = Query("nfse"),
    file_id: str = Query(""),
):
    kind = str(document_type or "").strip().lower()
    gateway = build_financial_received_invoice_gateway()
    authorization = str(get_request_authorization() or "")
    try:
        if kind == "nfse":
            content, filename = gateway.download_nfse_xml(
                authorization=authorization,
                document_id=document_id,
                variant=variant,
                branch=branch,
            )
        elif kind == "cte":
            content, filename = gateway.download_cte_xml(
                authorization=authorization,
                document_id=document_id,
                file_id=file_id,
                branch=branch,
            )
        else:
            return error_response(
                "O download de XML está disponível para NFS-e e CT-e.",
                status_code=422,
                code="VALIDATION_ERROR",
                recoverable=True,
            )
    except FinancialReceivedInvoiceGatewayError as exc:
        return _handle_financial(exc)
    except Exception as exc:
        log_error(f"Erro ao baixar XML fiscal no lançamento: {type(exc).__name__}")
        return error_response(
            "Erro ao obter o XML do documento fiscal.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    safe_name = "".join(ch for ch in filename if ch.isalnum() or ch in {".", "-", "_"}) or "nfse.xml"
    return Response(
        content=content,
        media_type="text/xml",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.post("/requests", operation_id="create_lancamento_notas_fiscais_request")
@require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)
def create_request(body: CreateRequestBody):
    try:
        branch_error = _gate_payload_branch(body.branch_code)
        if branch_error is not None:
            return branch_error
        data = build_received_invoice_attachment_service().execute(
            body.model_dump(by_alias=False),
            _actor(),
            authorization=str(get_request_authorization() or ""),
        )
        return api_delpi_success(
            data,
            operation_id="create_lancamento_notas_fiscais_request",
            message="Solicitação criada com sucesso.",
        )
    except FinancialReceivedInvoiceGatewayError as exc:
        return _handle_financial(exc)
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
    page_size: int = PAGE_SIZE_QUERY("page_20_100"),
):
    try:
        if branch:
            branch_error = _gate_payload_branch(branch)
            if branch_error is not None:
                return branch_error
        elif not has_global_branch_access():
            return error_response(
                "Informe a filial (parâmetro branch).",
                status_code=400,
                code="BRANCH_REQUIRED",
                recoverable=True,
            )
        try:
            resolve_list_status_filter(status)
        except ValueError as exc:
            return error_response(
                str(exc),
                status_code=400,
                code="INVALID_STATUS_FILTER",
                recoverable=True,
            )
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
        branch_error = _gate_loaded_branch(data)
        if branch_error is not None:
            return branch_error
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


@router.get(
    "/requests/{request_id}/danfe",
    operation_id="get_lancamento_notas_fiscais_request_danfe",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)
def download_request_danfe(
    request_id: UUID,
    disposition: str = Query("inline"),
):
    mode = str(disposition or "inline").strip().lower()
    if mode not in {"inline", "attachment"}:
        return error_response(
            "Disposição do arquivo inválida.",
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    try:
        data = build_get_invoice_posting_request_use_case().execute(str(request_id), _actor())
        branch_error = _gate_loaded_branch(data)
        if branch_error is not None:
            return branch_error
        attachment = data.get("danfe") if isinstance(data, dict) else None
        if not isinstance(attachment, dict):
            return not_found_response("DANFE não anexado a esta solicitação.", code="danfe.not_found")
        stored = build_invoice_posting_request_repository().get_danfe_attachment(str(request_id))
        if not isinstance(stored, dict) or not stored.get("stored_name"):
            return not_found_response("DANFE não anexado a esta solicitação.", code="danfe.not_found")
        content = LancamentoDanfeStorage().read(str(stored["stored_name"]))
    except LancamentoDanfeStorageError:
        return not_found_response("Arquivo do DANFE não encontrado.", code="danfe.not_found")
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao obter DANFE da solicitação LNF: {type(exc).__name__}")
        return error_response(
            "Erro ao obter o DANFE.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    filename = str(attachment.get("file_name") or stored.get("file_name") or "danfe.pdf")
    return _pdf_response(content, filename, mode)


@router.get(
    "/requests/{request_id}/fiscal-attachments/{attachment_type}",
    operation_id="get_lancamento_notas_fiscais_request_fiscal_attachment",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)
def download_request_fiscal_attachment(request_id: UUID, attachment_type: str):
    kind = str(attachment_type or "").strip().lower().replace("-", "_")
    if kind not in {"xml_original", "xml_standard", "dacte"}:
        return error_response(
            "Tipo de anexo fiscal inválido.",
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    try:
        data = build_get_invoice_posting_request_use_case().execute(str(request_id), _actor())
        branch_error = _gate_loaded_branch(data)
        if branch_error is not None:
            return branch_error
        stored = build_invoice_posting_request_repository().get_fiscal_attachment(str(request_id), kind)
        if not isinstance(stored, dict) or not stored.get("stored_name"):
            return not_found_response("Anexo fiscal não encontrado nesta solicitação.", code="fiscal_attachment.not_found")
        content = LancamentoFiscalAttachmentStorage().read(str(stored["stored_name"]))
    except LancamentoFiscalAttachmentStorageError:
        return not_found_response("Arquivo fiscal não encontrado.", code="fiscal_attachment.not_found")
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao obter XML da solicitação LNF: {type(exc).__name__}")
        return error_response(
            "Erro ao obter o XML da NFS-e.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    filename = str(stored.get("file_name") or (f"{kind}.pdf" if kind == "dacte" else f"{kind}.xml"))
    safe_name = "".join(ch for ch in filename if ch.isalnum() or ch in {".", "-", "_"}) or (
        "dacte.pdf" if kind == "dacte" else "fiscal.xml"
    )
    media_type = "application/pdf" if kind == "dacte" else "text/xml"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.get(
    "/requests/{request_id}/purchase-orders",
    operation_id="list_lancamento_notas_fiscais_request_purchase_orders",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)
def list_request_purchase_orders(request_id: UUID):
    try:
        data = build_list_request_open_purchase_orders_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = branch_access_error(str(data.get("branch_code") or ""))
        if branch_error is not None:
            return branch_error
        return api_delpi_success(
            data,
            operation_id="list_lancamento_notas_fiscais_request_purchase_orders",
            message="Pedidos de compra carregados.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao listar pedidos de compra LNF: {exc}")
        return error_response(
            "Erro ao consultar pedidos de compra no Protheus.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=True,
        )


@router.post(
    "/requests/{request_id}/purchase-orders/link",
    operation_id="link_lancamento_notas_fiscais_request_purchase_order",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_PROCESS_PERMISSIONS)
def link_request_purchase_order(request_id: UUID, body: LinkPurchaseOrderBody):
    try:
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
        data = build_link_request_purchase_order_use_case().execute(
            str(request_id),
            _actor(),
            groups=(
                [g.model_dump() for g in body.groups]
                if body.groups is not None
                else None
            ),
            order_number=body.order_number,
            delivery_date=body.delivery_date,
        )
        return api_delpi_success(
            data,
            operation_id="link_lancamento_notas_fiscais_request_purchase_order",
            message="Pedidos de compra amarrados à solicitação.",
        )
    except InvoicePostingError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"Erro ao amarrar pedido de compra LNF: {exc}")
        return error_response(
            "Erro ao amarrar pedido de compra.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=True,
        )


@router.patch(
    "/requests/{request_id}",
    operation_id="update_lancamento_notas_fiscais_request",
)
@require_any_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE_PERMISSIONS)
def update_request(request_id: UUID, body: dict[str, Any] = Body(...)):
    try:
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
        if "branch" in body or "branch_code" in body:
            target = body.get("branch_code", body.get("branch"))
            target_error = _gate_payload_branch(target)
            if target_error is not None:
                return target_error
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
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
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
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
        data = build_block_invoice_posting_request_use_case().execute(
            str(request_id),
            actor=_actor(),
            block_reason=body.block_reason,
            block_description=body.block_description,
            assignee_user_id=body.assignee_user_id,
            assignee_name=body.assignee_name,
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
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
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
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
        data = build_add_invoice_posting_comment_use_case().execute(
            str(request_id),
            actor=_actor(),
            body=body.body,
            mentioned_user_ids=body.mentioned_user_ids,
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
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
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
        current = build_get_invoice_posting_request_use_case().execute(
            str(request_id), _actor()
        )
        branch_error = _gate_loaded_branch(current)
        if branch_error is not None:
            return branch_error
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
